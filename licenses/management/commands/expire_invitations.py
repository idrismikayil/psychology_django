from django.core.management.base import BaseCommand
from django.utils import timezone
from licenses.models import TestInvitation


class Command(BaseCommand):
    help = 'Mark expired pending invitations as EXPIRED'

    def handle(self, *args, **options):
        count = TestInvitation.objects.filter(
            status='PENDING',
            expires_at__lt=timezone.now()
        ).update(status='EXPIRED')
        self.stdout.write(f'Expired {count} invitations.')
