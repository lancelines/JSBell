from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Creates a default superuser'

    def handle(self, *args, **kwargs):
        try:
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123456'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created superuser'))
        except IntegrityError:
            self.stdout.write(self.style.WARNING('Superuser already exists'))
