import time
from django.utils import timezone
from celery import shared_task
from django.db import transaction
import pandas as pd
from core.models import Client, Transaction
from core.models.transaction_statistics_view import TransactionStatistics
from core.models.etl_job import ETLJob
from .processors import ClientProcessor, DataProcessor, TransactionProcessor
from .metrics import (
    PROCESSED_RECORDS, PROCESSING_TIME, ACTIVE_JOBS,
    ERROR_COUNT, MEMORY_USAGE
)

@shared_task
def process_file(file_path: str, model, processor: DataProcessor, single_row_processing=False, chunk_size=1000) -> dict:
    start_time = time.time()
    processor_type = processor.__class__.__name__
    job = ETLJob.objects.create(
        job_name=f"Process {model.__name__} from {file_path}",
        status='running'
    )

    ACTIVE_JOBS.labels(processor_type=processor_type).inc()

    try:
        processed_count = 0
        db_errors = []

        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        valid_records, failed_count, errors = processor.process_data(df)

        if errors:
            ERROR_COUNT.labels(
                processor_type=processor_type,
                error_type='validation'
            ).inc(len(errors))

        if single_row_processing:
            for record in valid_records:
                try:
                    model.objects.create(**record)
                    processed_count += 1
                except Exception as e:
                    db_errors.append({
                        'row': record,
                        'error': f'Database error: {str(e)}'
                    })
        else:
            with transaction.atomic():
                for i in range(0, len(valid_records), chunk_size):
                    chunk = valid_records[i:i + chunk_size]
                    try:
                        instances = [model(**record) for record in chunk]
                        model.objects.bulk_create(instances, ignore_conflicts=True)
                        processed_count += len(chunk)
                    except Exception as e:
                        db_errors.append({
                            'chunk_start': i,
                            'chunk_size': len(chunk),
                            'error': f'Bulk insert error: {str(e)}'
                        })

        # Move the metrics increment AFTER processing is done
        PROCESSED_RECORDS.labels(
            processor_type=processor_type,
            status='success'
        ).inc(processed_count)

        if model == Transaction:
            TransactionStatistics.refresh()

        all_errors = {
            'validation_errors': errors,
            'database_errors': db_errors
        }

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.records_processed = processed_count
        job.save()

        # Record processing time at the end
        PROCESSING_TIME.labels(
            processor_type=processor_type,
            operation='total'
        ).observe(time.time() - start_time)

        # Decrease active jobs counter
        ACTIVE_JOBS.labels(processor_type=processor_type).dec()

        return {
            'success': True,
            'message': f'Successfully processed {processed_count} records. Failed: {failed_count}',
            'processed_count': processed_count,
            'failed_count': failed_count,
            'errors': all_errors
        }
    except Exception as e:
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.save()

        # Record processing time and decrease active jobs even on failure
        PROCESSING_TIME.labels(
            processor_type=processor_type,
            operation='total'
        ).observe(time.time() - start_time)

        ACTIVE_JOBS.labels(processor_type=processor_type).dec()

        return {
            'success': False,
            'message': str(e),
            'error': str(e)
        }

@shared_task
def process_clients_file(file_path: str, single_row_processing=False, chunk_size=1000) -> dict:
    processor = ClientProcessor()
    return process_file(file_path, Client, processor, single_row_processing, chunk_size)

@shared_task
def process_transactions_file(file_path: str, single_row_processing=False, chunk_size=1000) -> dict:
    processor = TransactionProcessor()
    return process_file(file_path, Transaction, processor, single_row_processing, chunk_size)