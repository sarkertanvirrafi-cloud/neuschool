import os
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Validate required production environment variables without printing secrets.'

    def handle(self, *args, **options):
        required = ['DJANGO_SECRET_KEY', 'DATABASE_URL', 'VDOCIPHER_API_SECRET']
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise CommandError('Missing required production variables: ' + ', '.join(missing))

        optional = ['CLOUDINARY_URL', 'VDOCIPHER_ALLOWED_DOMAIN']
        missing_optional = [name for name in optional if not os.getenv(name)]
        self.stdout.write(self.style.SUCCESS('Required production variables are configured.'))
        if missing_optional:
            self.stdout.write(self.style.WARNING(
                'Recommended variables not configured: ' + ', '.join(missing_optional)
            ))
