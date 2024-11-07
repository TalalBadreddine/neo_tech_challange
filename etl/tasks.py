from celery import shared_task
from django.db import transaction
import pandas as pd
from core.models import Client, Transaction
from core.models.transaction_statistics_view import TransactionStatistics
from .processors import ClientProcessor, DataProcessor, TransactionProcessor

# TODO: decide if we want to handle each row individually or in bulk, to not roll back all rows on failure
@shared_task
def process_file(file_path: str, model, processor: DataProcessor) -> dict:
    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        df = processor.clean_dataframe(df)

        processed_count = 0
        with transaction.atomic():
            for _, row in df.iterrows():
                processed_data = processor.process_row(row)
                if processed_data:
                    model.objects.update_or_create(**processed_data)
                    processed_count += 1

        TransactionStatistics.refresh()
        return {
            'success': True,
            'message': f'Successfully processed {processed_count} records',
            'processed_count': processed_count
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'error': e
        }

@shared_task
def process_clients_file(file_path: str) -> dict:
    processor = ClientProcessor()
    return process_file(file_path, Client, processor)

@shared_task
def process_transactions_file(file_path: str) -> dict:
    processor = TransactionProcessor()
    return process_file(file_path, Transaction, processor)