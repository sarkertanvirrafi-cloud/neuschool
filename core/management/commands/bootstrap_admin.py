import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update the initial NeuSchool staff/superuser from environment variables.'

    def handle(self, *args, **options):
        email = os.getenv('ADMIN_EMAIL', '').strip().lower()
        password = os.getenv('ADMIN_PASSWORD', '')
        name = os.getenv('ADMIN_NAME', 'NeuSchool Admin').strip()
        if not email or not password:
            self.stdout.write('ADMIN_EMAIL / ADMIN_PASSWORD not set; skipping admin bootstrap.')
            return

        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'first_name': name, 'is_staff': True, 'is_superuser': True},
        )
        user.email = email
        user.first_name = name
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} admin {email}."))
