from django.core.management.base import BaseCommand
from django.conf import settings
from backend.utils.email import send_html_email

class Command(BaseCommand):
    help = 'Send a test HTML email to a specified address using configured SMTP settings.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address for test email')

    def handle(self, *args, **options):
        recipient = options['email']
        subject = 'Test Email from Booking App'
        content = 'This is a test email sent from the Booking App to verify SMTP configuration.'
        details = 'This email verifies that your SMTP settings are correct.'

        send_html_email(subject=subject, to_email=recipient, content=content, details=details, from_email=settings.DEFAULT_FROM_EMAIL, fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f'Sent test email to {recipient}'))
