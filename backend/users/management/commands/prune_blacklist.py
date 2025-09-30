from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import RefreshTokenBlacklist


class Command(BaseCommand):
    help = 'Prune expired entries from the RefreshTokenBlacklist table'

    def handle(self, *args, **options):
        now = timezone.now()
        # Remove rows with expires_at set and in the past
        expired_qs = RefreshTokenBlacklist.objects.filter(expires_at__isnull=False, expires_at__lt=now)
        count = expired_qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired blacklist entries found.'))
            return

        expired_qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} expired blacklist entr{"ies" if count != 1 else "y"}.'))
