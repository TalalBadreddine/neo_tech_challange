from django.utils import timezone
from celery import shared_task
from django.db import transaction
import pandas as pd
from core.models import Client, Transaction
from core.models.transaction_statistics_view import TransactionStatistics
from core.models.etl_job import ETLJob
from .processors import ClientProcessor, DataProcessor, TransactionProcessor
from core.logging import logger

@shared_task
def process_file(file_path: str, model, processor: DataProcessor, single_row_processing=False, chunk_size=1000) -> dict:
    job = ETLJob.objects.create(
        job_name=f"Process {model.__name__} from {file_path}",
        status='running'
    )

    logger.info("Starting file processing", extra={
        'component': 'etl_processor',
        'action': 'process_start',
        'job_id': job.id,
        'model': model.__name__,
        'file_path': file_path,
        'chunk_size': chunk_size
    })

    try:

        df = (pd.read_csv(file_path, engine='c') if file_path.endswith('.csv')
              else pd.read_excel(file_path, engine='openpyxl'))
        logger.info("File loaded successfully", extra={
            'component': 'etl_processor',
            'action': 'file_loaded',
            'job_id': job.id,
            'row_count': len(df)
        })


        valid_records, validation_failed_count, validation_errors = processor.process_data(df)

        if validation_errors:
            logger.warning("Validation errors found during processing", extra={
                'component': 'etl_processor',
                'action': 'validation_errors',
                'job_id': job.id,
                'validation_failed_count': validation_failed_count,
                'validation_errors': validation_errors
            })

        processed_count = 0
        db_failed_count = 0
        db_errors = []


        for i in range(0, len(valid_records), chunk_size):
            chunk = valid_records[i:i + chunk_size]
            logger.info("Processing chunk", extra={
                'component': 'etl_processor',
                'action': 'chunk_start',
                'job_id': job.id,
                'chunk_index': i,
                'chunk_size': len(chunk)
            })

            try:
                with transaction.atomic():
                    initial_count = model.objects.count()
                    instances = [model(**record) for record in chunk]
                    model.objects.bulk_create(instances, ignore_conflicts=True)
                    final_count = model.objects.count()

                    actually_created = final_count - initial_count
                    failed_in_chunk = len(chunk) - actually_created

                    processed_count += actually_created
                    db_failed_count += failed_in_chunk

                    logger.info("Chunk processed", extra={
                        'component': 'etl_processor',
                        'action': 'chunk_complete',
                        'job_id': job.id,
                        'chunk_index': i,
                        'records_created': actually_created,
                        'records_failed': failed_in_chunk
                    })

            except Exception as e:
                logger.error("Bulk insert failed, attempting individual inserts", extra={
                    'component': 'etl_processor',
                    'action': 'bulk_insert_failed',
                    'job_id': job.id,
                    'chunk_index': i,
                    'error': str(e)
                })

                for record in chunk:
                    try:
                        with transaction.atomic():
                            model.objects.create(**record)
                            processed_count += 1
                    except Exception as individual_error:
                        db_failed_count += 1
                        error_detail = {
                            'row': record,
                            'error': f'Individual insert error: {str(individual_error)}'
                        }
                        db_errors.append(error_detail)
                        logger.error("Individual record insertion failed", extra={
                            'component': 'etl_processor',
                            'action': 'record_insert_failed',
                            'job_id': job.id,
                            'error': str(individual_error),
                            'record': record
                        })

        if model == Transaction:
            TransactionStatistics.refresh()

        total_failed_count = validation_failed_count + db_failed_count


        logger.info("File processing completed", extra={
            'component': 'etl_processor',
            'action': 'process_complete',
            'job_id': job.id,
            'statistics': {
                'total_rows': processed_count + total_failed_count,
                'processed_count': processed_count,
                'failed_count': total_failed_count,
                'validation_failed_count': validation_failed_count,
                'db_failed_count': db_failed_count,
                'success_rate': f"{(processed_count / (processed_count + total_failed_count) * 100):.2f}%" if (processed_count + total_failed_count) > 0 else "0%"
            }
        })

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.records_processed = processed_count
        job.save()

        return {
            'success': True,
            'message': f'Successfully processed {processed_count} records. Failed: {total_failed_count}',
            'processed_count': processed_count,
            'failed_count': total_failed_count,
            'validation_failed_count': validation_failed_count,
            'db_failed_count': db_failed_count,
            'total_rows': processed_count + total_failed_count,
            'success_rate': (processed_count / (processed_count + total_failed_count) * 100) if (processed_count + total_failed_count) > 0 else 0,
            'errors': {
                'validation_errors': validation_errors,
                'database_errors': db_errors
            }
        }

    except Exception as e:
        logger.error("File processing failed", extra={
            'component': 'etl_processor',
            'action': 'process_failed',
            'job_id': job.id,
            'error': str(e)
        })

        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_message = str(e)
        job.save()

        return {
            'success': False,
            'message': str(e),
            'error': str(e),
            'processed_count': 0,
            'failed_count': 0,
            'validation_failed_count': 0,
            'db_failed_count': 0,
            'total_rows': 0,
            'success_rate': 0,
            'errors': {
                'validation_errors': [],
                'database_errors': []
            }
        }

@shared_task
def process_clients_file(file_path: str, single_row_processing=False, chunk_size=1000) -> dict:
    processor = ClientProcessor()
    return process_file(file_path, Client, processor, single_row_processing, chunk_size)

@shared_task
def process_transactions_file(file_path: str, single_row_processing=False, chunk_size=1000) -> dict:
    processor = TransactionProcessor()
    return process_file(file_path, Transaction, processor, single_row_processing, chunk_size)