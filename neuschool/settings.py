from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-change-me-before-production')
DEBUG = os.getenv('DJANGO_DEBUG', '0' if os.getenv('VERCEL') else '1') == '1'

ALLOWED_HOSTS = [
    host.strip() for host in os.getenv(
        'DJANGO_ALLOWED_HOSTS',
        'localhost,127.0.0.1,.vercel.app'
    ).split(',') if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        'https://*.vercel.app'
    ).split(',') if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'neuschool.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'neuschool.wsgi.application'
ASGI_APPLICATION = 'neuschool.asgi.application'

DATABASE_URL = os.getenv("NEUSCHOOL_DATABASE_URL") or os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'Asia/Dhaka')
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/auth/'
LOGIN_REDIRECT_URL = '/courses/'
LOGOUT_REDIRECT_URL = '/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv('DJANGO_SECURE_SSL_REDIRECT', '1') == '1'
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_HSTS_SECONDS', '3600'))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
SITE_ADDRESS = os.getenv('SITE_ADDRESS', 'Address will be added here.')
SITE_CONTACT = os.getenv('SITE_CONTACT', 'Contact info will be added here.')

# VdoCipher DRM (server-side secret only)
VDOCIPHER_API_SECRET = os.getenv('VDOCIPHER_API_SECRET', '')
VDOCIPHER_FOLDER_ID = os.getenv('VDOCIPHER_FOLDER_ID', '')
VDOCIPHER_ALLOWED_DOMAIN = os.getenv('VDOCIPHER_ALLOWED_DOMAIN', '')
VDOCIPHER_OTP_TTL = int(os.getenv('VDOCIPHER_OTP_TTL', '300'))
VDOCIPHER_WATERMARK_ENABLED = os.getenv('VDOCIPHER_WATERMARK_ENABLED', '1') == '1'

SESSION_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = 'same-origin'
