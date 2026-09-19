"""VdoCipher server-side integration.

The API secret must only exist on the server. Playback tokens are generated only
after NeuSchool verifies authentication and course enrollment.
"""

import json
import logging
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VDOCIPHER_API_BASE = 'https://dev.vdocipher.com/api'
VDOCIPHER_PLAYER_BASE = 'https://player.vdocipher.com/v2/'


class DRMConfigurationError(RuntimeError):
    pass


class DRMServiceError(RuntimeError):
    pass


def _secret():
    secret = getattr(settings, 'VDOCIPHER_API_SECRET', '')
    if not secret:
        raise DRMConfigurationError('VDOCIPHER_API_SECRET is not configured.')
    return secret


def _headers():
    return {
        'Authorization': f'Apisecret {_secret()}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }


def _safe_error(response):
    try:
        payload = response.json()
        return str(payload.get('message') or payload.get('error') or payload)[:500]
    except Exception:
        return f'HTTP {response.status_code}'


def generate_playback(video_id, user):
    if not video_id:
        raise DRMServiceError('This lecture does not have a DRM video ID.')

    ttl = max(60, min(int(getattr(settings, 'VDOCIPHER_OTP_TTL', 300)), 3600))
    payload = {
        'ttl': ttl,
        # VdoCipher recommends a non-PII internal identifier for viewer analytics.
        'userId': f'u{user.pk}',
    }

    if getattr(settings, 'VDOCIPHER_WATERMARK_ENABLED', True):
        display_name = (user.get_full_name() or user.username or f'User {user.pk}').strip()
        watermark = f'NeuSchool • {display_name[:48]} • ID {user.pk}'
        payload['annotate'] = json.dumps([
            {
                'type': 'rtext',
                'text': watermark,
                'alpha': '0.45',
                'color': '0xFFFFFF',
                'size': '14',
                'interval': '5000',
                'skip': '5000',
            }
        ])

    allowed_domain = getattr(settings, 'VDOCIPHER_ALLOWED_DOMAIN', '').strip()
    if allowed_domain:
        payload['whitelisthref'] = allowed_domain

    url = f'{VDOCIPHER_API_BASE}/videos/{quote(video_id, safe="")}/otp'
    try:
        response = requests.post(url, headers=_headers(), json=payload, timeout=12)
    except requests.RequestException as exc:
        logger.warning('VdoCipher playback request failed: %s', exc.__class__.__name__)
        raise DRMServiceError('Secure video service is temporarily unavailable.') from exc

    if not response.ok:
        logger.warning('VdoCipher playback returned %s: %s', response.status_code, _safe_error(response))
        raise DRMServiceError('Secure video is processing or temporarily unavailable.')

    data = response.json()
    otp = data.get('otp')
    playback_info = data.get('playbackInfo')
    if not otp or not playback_info:
        raise DRMServiceError('Secure video service returned an incomplete playback token.')

    player_url = (
        f'{VDOCIPHER_PLAYER_BASE}?otp={quote(str(otp), safe="")}'
        f'&playbackInfo={quote(str(playback_info), safe="")}'
        '&primaryColor=0A84D8&litemode=true'
    )
    return {'otp': otp, 'playbackInfo': playback_info, 'playerUrl': player_url}


def create_upload_credentials(title):
    """Create temporary browser-upload credentials without exposing API secret."""
    title = (title or '').strip()[:240]
    if not title:
        raise DRMServiceError('A video title is required.')

    params = {'title': title}
    folder_id = getattr(settings, 'VDOCIPHER_FOLDER_ID', '').strip()
    if folder_id:
        params['folderId'] = folder_id

    url = f'{VDOCIPHER_API_BASE}/videos'
    try:
        response = requests.put(url, headers=_headers(), params=params, timeout=12)
    except requests.RequestException as exc:
        logger.warning('VdoCipher upload credential request failed: %s', exc.__class__.__name__)
        raise DRMServiceError('Could not start secure video upload.') from exc

    if not response.ok:
        logger.warning('VdoCipher upload credentials returned %s: %s', response.status_code, _safe_error(response))
        raise DRMServiceError('Could not create secure upload credentials.')

    data = response.json()
    video_id = data.get('videoId') or data.get('video_id')
    client_payload = data.get('clientPayload') or data.get('clientPayLoad')
    if not video_id or not isinstance(client_payload, dict) or not client_payload.get('uploadLink'):
        raise DRMServiceError('Secure upload service returned incomplete credentials.')

    # Return only the short-lived browser upload policy and new video ID.
    return {'videoId': video_id, 'clientPayload': client_payload}
