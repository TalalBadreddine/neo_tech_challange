import json
import os
import subprocess
import time
from django.core.management.base import BaseCommand
from etl.tasks import process_clients_file, process_transactions_file
from core.logging import logger


class Command(BaseCommand):
    help = 'Run ETL process for clients and transactions'

    def add_arguments(self, parser):
        parser.add_argument('--clients-file', type=str, help='Path to clients CSV/Excel file')
        parser.add_argument('--transactions-file', type=str, help='Path to transactions CSV/Excel file')
        parser.add_argument('--verbose', action='store_true', help='Prints verbose output')

    def start_celery_worker(self):
        """Start Celery worker process"""
        try:
            logger.info("Starting Celery worker process", extra={
                'component': 'celery',
                'action': 'worker_start'
            })

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
                    logger.info("Celery worker ready", extra={
                        'component': 'celery',
                        'action': 'worker_ready'
                    })
                    return process
                if process.poll() is not None:
                    error = process.stderr.read()
                    logger.error("Celery worker failed to start", extra={
                        'component': 'celery',
                        'action': 'worker_failed',
                        'error': error
                    })
                    return None

        except Exception as e:
            logger.error("Failed to start Celery worker", extra={
                'component': 'celery',
                'action': 'worker_failed',
                'error': str(e)
            })
            return None

    def handle(self, *args, **options):
        logger.info("ETL process initiated", extra={
            'component': 'etl',
            'action': 'process_start',
            'configuration': {
                'clients_file': options.get('clients_file'),
                'transactions_file': options.get('transactions_file'),
                'verbose': options.get('verbose')
            }
        })

        worker_process = self.start_celery_worker()
        if not worker_process:
            logger.error("ETL process aborted - worker failed to start", extra={
                'component': 'etl',
                'action': 'process_abort'
            })
            return

        try:
            tasks = []

            if options['clients_file']:
                task = process_clients_file.delay(
                    options['clients_file']
                )
                tasks.append(('clients', task))
                logger.info("Client processing task created", extra={
                    'component': 'etl',
                    'action': 'task_created',
                    'task_type': 'clients',
                    'task_id': task.id,
                    'file_path': options['clients_file']
                })

            if options['transactions_file']:
                task = process_transactions_file.delay(
                    options['transactions_file']
                )
                tasks.append(('transactions', task))
                logger.info("Transaction processing task created", extra={
                    'component': 'etl',
                    'action': 'task_created',
                    'task_type': 'transactions',
                    'task_id': task.id,
                    'file_path': options['transactions_file']
                })

            while tasks:
                for task_type, task in tasks[:]:
                    if task.ready():
                        result = task.get()
                        if result.get('success'):
                            total_rows = result.get('processed_count', 0) + result.get('failed_count', 0)
                            successful_rows = result.get('processed_count', 0)
                            failed_rows = result.get('failed_count', 0)
                            validation_errors_count = result.get('validation_failed_count', 0)
                            database_errors_count = result.get('db_failed_count', 0)
                            success_rate = (successful_rows / total_rows * 100) if total_rows > 0 else 0

                            stats = {
                                'total_rows': total_rows,
                                'processed_count': successful_rows,
                                'failed_count': failed_rows,
                                'validation_failed_count': validation_errors_count,
                                'db_failed_count': database_errors_count,
                                'success_rate': f"{success_rate:.2f}%"
                            }

                            logger.info(f"{task_type.title()} processing completed", extra={
                                'component': 'etl',
                                'action': 'task_completed',
                                'task_type': task_type,
                                'task_id': task.id,
                                'statistics': stats
                            })

                            self.stdout.write(self.style.SUCCESS(
                                f"\nProcessing Statistics for {task_type.title()}:"
                                f"\n- Total Rows: {total_rows}"
                                f"\n- Successfully Processed: {successful_rows}"
                                f"\n- Total Failed: {failed_rows}"
                                f"\n  • Validation Errors: {validation_errors_count}"
                                f"\n  • Database Errors: {database_errors_count}"
                                f"\n- Success Rate: {success_rate:.2f}%"
                            ))

                            if result.get('errors') and options['verbose']:
                                validation_errors = result['errors'].get('validation_errors', [])
                                if validation_errors:
                                    logger.warning("Validation errors detected", extra={
                                        'component': 'etl',
                                        'action': 'validation_errors',
                                        'task_type': task_type,
                                        'task_id': task.id,
                                        'errors': validation_errors
                                    })
                                    self.stdout.write(self.style.WARNING(
                                        "\nValidation Errors:"
                                        f"\n{json.dumps(validation_errors, indent=2, default=str)}"
                                    ))

                                database_errors = result['errors'].get('database_errors', [])
                                if database_errors:
                                    logger.error("Database errors detected", extra={
                                        'component': 'etl',
                                        'action': 'database_errors',
                                        'task_type': task_type,
                                        'task_id': task.id,
                                        'errors': database_errors
                                    })
                                    self.stdout.write(self.style.ERROR(
                                        "\nDatabase Errors:"
                                        f"\n{json.dumps(database_errors, indent=2, default=str)}"
                                    ))
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error("Task execution failed", extra={
                                'component': 'etl',
                                'action': 'task_failed',
                                'task_type': task_type,
                                'task_id': task.id,
                                'error': error_msg
                            })
                            self.stdout.write(self.style.ERROR(
                                f"\n{task_type.title()} task failed: {error_msg}"
                            ))
                        tasks.remove((task_type, task))

                if tasks:
                    time.sleep(1)

            logger.info("ETL process completed", extra={
                'component': 'etl',
                'action': 'process_complete'
            })

        except Exception as e:
            logger.error("ETL process failed", extra={
                'component': 'etl',
                'action': 'process_failed',
                'error': str(e)
            })
            self.stdout.write(self.style.ERROR(f"\nETL process failed: {str(e)}"))

        finally:
            if worker_process and worker_process.poll() is None:
                worker_process.terminate()
                worker_process.wait()
                logger.info("Celery worker shutdown", extra={
                    'component': 'celery',
                    'action': 'worker_shutdown'
                })