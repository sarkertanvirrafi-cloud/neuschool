import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.text import slugify


def upload_asset(uploaded_file, folder='neuschool', resource_type='auto'):
    """Upload to Cloudinary in production; use local MEDIA_ROOT during development."""
    if settings.CLOUDINARY_URL:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(secure=True)
        stem = slugify(Path(uploaded_file.name).stem) or 'file'
        public_id = f'{stem}-{uuid.uuid4().hex[:10]}'
        result = cloudinary.uploader.upload(
            uploaded_file,
            folder=folder,
            public_id=public_id,
            resource_type=resource_type,
            overwrite=False,
        )
        return result['secure_url']

    fs = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    safe_name = f'{uuid.uuid4().hex[:10]}-{os.path.basename(uploaded_file.name)}'
    stored = fs.save(f'{folder}/{safe_name}', uploaded_file)
    return fs.url(stored)
