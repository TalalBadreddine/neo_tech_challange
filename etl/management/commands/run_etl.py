from django.core.management.base import BaseCommand
from etl.tasks import process_clients_file, process_transactions_file

class Command(BaseCommand):
    help = 'Run ETL process for clients and transactions'

    def add_arguments(self, parser):
        parser.add_argument('--clients-file', type=str, help='Path to clients CSV/Excel file')
        parser.add_argument('--transactions-file', type=str, help='Path to transactions CSV/Excel file')

    def handle(self, *args, **options):
        if options['clients_file']:
            result = process_clients_file(options['clients_file'])
            self.stdout.write(
                self.style.SUCCESS(result['message']) if result['success']
                else self.style.ERROR(result['message'])
            )

        if options['transactions_file']:
            result = process_transactions_file(options['transactions_file'])
            self.stdout.write(
                self.style.SUCCESS(result['message']) if result['success']
                else self.style.ERROR(result['message'])
            )