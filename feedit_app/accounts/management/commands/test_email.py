from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='to_email',
            default='geraghtyglenn@gmail.com',
            help='Recipient email address',
        )

    def handle(self, *args, **options):
        to_email = options['to_email']
        from_email = settings.DEFAULT_FROM_EMAIL
        
        self.stdout.write(f"Sending test email from {from_email} to {to_email}...")
        
        try:
            result = send_mail(
                subject='Test Email from Feedit (Django)',
                message='This is a test email sent from Feedit using MailerSend SMTP configuration via Django.',
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(self.style.SUCCESS('Test email sent successfully!'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send email. Result: {result}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error sending email: {e}'))
