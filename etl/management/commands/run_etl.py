from django.core.management.base import BaseCommand
from etl.tasks import process_clients_file, process_transactions_file

class Command(BaseCommand):
    help = 'Run ETL process for clients and transactions'

    def add_arguments(self, parser):
        parser.add_argument('--clients-file', type=str, help='Path to clients CSV/Excel file')
        parser.add_argument('--transactions-file', type=str, help='Path to transactions CSV/Excel file')
        parser.add_argument('--single-row-processing', action='store_true', help='Inserts row individually into db')

    def handle(self, *args, **options):
        if options['clients_file']:
            task = process_clients_file.delay(options['clients_file'], single_row_processing=options['single_row_processing'])
            self.stdout.write(self.style.SUCCESS(f'Processing clients file: {options["clients_file"]}. Task ID: {task.id}'))


        if options['transactions_file']:
            task = process_transactions_file.delay(options['transactions_file'], single_row_processing=options['single_row_processing'])
            self.stdout.write(self.style.SUCCESS(f'Processing transactions file: {options["transactions_file"]}. Task ID: {task.id}'))