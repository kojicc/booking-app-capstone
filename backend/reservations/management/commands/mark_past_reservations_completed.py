from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from backend.reservations.models import Reservation, ReservationAuditLog

class Command(BaseCommand):
    help = 'Mark reservations in the past as COMPLETED and write audit logs (idempotent)'

    def handle(self, *args, **options):
        today = date.today()
        # Select reservations strictly before today and still pending/confirmed
        qs = Reservation.objects.filter(date__lt=today, status__in=['PENDING', 'CONFIRMED'])
        total = qs.count()
        updated = 0

        for r in qs:
            old_status = r.status
            r.status = 'COMPLETED'
            r.save(update_fields=['status', 'updated_at'])

            # Create an audit log entry
            try:
                ReservationAuditLog.objects.create(
                    reservation=r,
                    action='UPDATED',
                    performed_by=r.user,
                    details={'change': f'status {old_status} -> COMPLETED by management command'}
                )
            except Exception:
                # Don't stop the command for audit failures
                pass

            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Marked {updated} of {total} past reservations as COMPLETED'))
