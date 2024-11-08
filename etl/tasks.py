from django.utils import timezone
from celery import shared_task
from django.db import transaction
import pandas as pd
from core.models import Client, Transaction
from core.models.transaction_statistics_view import TransactionStatistics
from core.models.etl_job import ETLJob
from .processors import ClientProcessor, DataProcessor, TransactionProcessor

@shared_task
def process_file(file_path: str, model, processor: DataProcessor, single_row_processing=False, chunk_size=1000) -> dict:

    job = ETLJob.objects.create(
        job_name=f"Process {model.__name__} from {file_path}",
        status='running'
    )

    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df = processor.clean_dataframe(df)

        processed_count = 0
        errors = []
        valid_data = []

        for _, row in df.iterrows():
            try:
                processed_data = processor.process_row(row)
                if processed_data:
                    valid_data.append(processed_data)
                else:
                    errors.append({'row': row.to_dict(), 'error': 'Invalid data.'})
            except Exception as e:
                errors.append({'row': row.to_dict(), 'error': str(e)})

        if single_row_processing:
            for data in valid_data:
                try:
                    model.objects.update_or_create(**data)
                    processed_count += 1
                except Exception as e:
                    errors.append({'row': row.to_dict(), 'error': str(e)})
        else:
            with transaction.atomic():
                for i in range(0, len(valid_data), chunk_size):
                    chunk = valid_data[i:i + chunk_size]
                    model.objects.bulk_create([model(**data) for data in chunk], ignore_conflicts=True)
                    processed_count += len(chunk)

        if model == Transaction:
            TransactionStatistics.refresh()

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.records_processed = processed_count
        job.save()

        return {
            'success': True,
            'message': f'Successfully processed {processed_count} records',
            'processed_count': processed_count
        }
    except Exception as e:

        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.save()

        return {
            'success': False,
            'message': str(e),
            'error': str(e)
        }

@shared_task
def process_clients_file(file_path: str, single_row_processing=False) -> dict:
    processor = ClientProcessor()
    return process_file(file_path, Client, processor, single_row_processing)

@shared_task
def process_transactions_file(file_path: str, single_row_processing=False) -> dict:
    processor = TransactionProcessor()
    return process_file(file_path, Transaction, processor, single_row_processing)