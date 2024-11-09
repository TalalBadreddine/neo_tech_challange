import os
import subprocess
import time
from django.core.management.base import BaseCommand
from etl.tasks import process_clients_file, process_transactions_file

class Command(BaseCommand):
    help = 'Run ETL process for clients and transactions'

    def add_arguments(self, parser):
        parser.add_argument('--clients-file', type=str, help='Path to clients CSV/Excel file')
        parser.add_argument('--transactions-file', type=str, help='Path to transactions CSV/Excel file')
        parser.add_argument('--single-row-processing', action='store_true', help='Inserts row individually into db')
        parser.add_argument('--verbose', action='store_true', help='Prints verbose output')

    def start_celery_worker(self):
        """Start Celery worker process"""
        try:
            self.stdout.write('Starting Celery worker...')


            celery_cmd = 'celery -A neo_challenge worker -l info'
            process = subprocess.Popen(
                celery_cmd.split(),
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                output = process.stdout.readline()
                if "[tasks]" in output:
                    self.stdout.write(self.style.SUCCESS('Celery worker is ready!'))
                    return process
                if process.poll() is not None:
                    error = process.stderr.read()
                    self.stdout.write(self.style.ERROR(f'Worker failed to start: {error}'))
                    return None

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to start Celery worker: {e}'))
            return None

    def handle(self, *args, **options):
        worker_process = self.start_celery_worker()
        if not worker_process:
            self.stdout.write(self.style.ERROR('Failed to start worker. Exiting.'))
            return

        try:
            tasks = []

            if options['clients_file']:
                task = process_clients_file.delay(
                    options['clients_file'],
                    single_row_processing=options['single_row_processing']
                )
                tasks.append(('clients', task))
                self.stdout.write(self.style.SUCCESS(
                    f'Processing clients file: {options["clients_file"]}. Task ID: {task.id}'
                ))

            if options['transactions_file']:
                task = process_transactions_file.delay(
                    options['transactions_file'],
                    single_row_processing=options['single_row_processing']
                )
                tasks.append(('transactions', task))
                self.stdout.write(self.style.SUCCESS(
                    f'Processing transactions file: {options["transactions_file"]}. Task ID: {task.id}'
                ))

            while tasks:
                for task_type, task in tasks[:]:
                    if task.ready():
                        result = task.get()
                        if result.get('success'):
                            self.stdout.write(self.style.SUCCESS(
                                f'{task_type.title()} task completed: {result["message"]}'
                            ))

                            if options['verbose']:
                                self.stdout.write(f"RESULTS: {result}")
                                if result.get('errors'):
                                    self.stdout.write(self.style.WARNING('Errors encountered:'))

                            if result['errors'].get('validation_errors') and options['verbose']:
                                self.stdout.write(self.style.WARNING('Validation Errors:'))
                                for error in result['errors']['validation_errors']:
                                    self.stdout.write(f"Row: {error['row']}")
                                    self.stdout.write(f"Error: {error['error']}")
                                    self.stdout.write("---")

                            if result['errors'].get('database_errors') and options['verbose']:
                                self.stdout.write(self.style.WARNING('Database Errors:'))
                                for error in result['errors']['database_errors']:
                                    self.stdout.write(f"Error: {error['error']}")
                                    self.stdout.write("---")
                        else:
                            self.stdout.write(self.style.ERROR(
                                f'{task_type.title()} task failed: {result.get("error", "Unknown error")}'
                            ))
                        tasks.remove((task_type, task))

                if tasks:
                    time.sleep(1)

            self.stdout.write(self.style.SUCCESS('All tasks completed!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during processing: {str(e)}'))

        finally:

            if worker_process and worker_process.poll() is None:
                worker_process.terminate()
                worker_process.wait()
                self.stdout.write('Celery worker stopped.')