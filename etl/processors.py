import time
from typing import Optional, Tuple, List, Dict
import pandas as pd
from .validators import validate_client, validate_transaction
import logging
import json
import structlog

from .metrics import (
    PROCESSED_RECORDS, PROCESSING_TIME, ACTIVE_JOBS,
    ERROR_COUNT, MEMORY_USAGE
)

logger = structlog.get_logger()

class DataProcessor:
    def __init__(self):
        self.processor_type = self.__class__.__name__

    def log_error(self, error_type: str, error_message: str, row_data: dict, row_index: int):
        logger.error(
            "ETL processing error",
            processor_type=self.processor_type,
            error_type=error_type,
            error_message=error_message,
            row_index=row_index,
            row_data=json.dumps(row_data)
        )

    def process_data(self, df: pd.DataFrame) -> Tuple[List[Dict], int, List[Dict]]:
        start_time = time.time()
        total_rows = len(df)

        PROCESSED_RECORDS.labels(
            processor_type=self.processor_type,
            status='total'
        ).inc(total_rows)

        ACTIVE_JOBS.labels(processor_type=self.processor_type).inc()

        try:
            valid_records = []
            errors = []

            for index, row in df.iterrows():
                try:
                    record, error = self.process_row(row)
                    if record and not error:
                        valid_records.append(record)
                        PROCESSED_RECORDS.labels(
                            processor_type=self.processor_type,
                            status='success'
                        ).inc()
                    else:
                        error_detail = {
                            'row_index': index + 1,
                            'error_type': 'validation',
                            'error_message': error,
                            'data': row.to_dict()
                        }
                        errors.append(error_detail)

                        ERROR_COUNT.labels(
                            processor_type=self.processor_type,
                            error_type='validation'
                        ).inc()

                        self.log_error(
                            'validation',
                            error,
                            row.to_dict(),
                            index + 1
                        )

                except Exception as e:
                    error_detail = {
                        'row_index': index + 1,
                        'error_type': 'processing',
                        'error_message': str(e),
                        'data': row.to_dict()
                    }
                    errors.append(error_detail)

                    ERROR_COUNT.labels(
                        processor_type=self.processor_type,
                        error_type='processing'
                    ).inc()

                    self.log_error(
                        'processing',
                        str(e),
                        row.to_dict(),
                        index + 1
                    )

            return valid_records, len(errors), errors
        finally:
            PROCESSING_TIME.labels(
                processor_type=self.processor_type,
                operation='total'
            ).observe(time.time() - start_time)

            ACTIVE_JOBS.labels(processor_type=self.processor_type).dec()

class ClientProcessor(DataProcessor):
    def process_row(self, row) -> Tuple[Optional[dict], Optional[str]]:
        cleaned_data, errors = validate_client(row)

        if errors:
            return None, '; '.join(errors)

        return {
            'client_id': cleaned_data['client_id'],
            'name': cleaned_data['name'],
            'email': cleaned_data['email'],
            'date_of_birth': cleaned_data['date_of_birth'],
            'country': cleaned_data['country'],
            'account_balance': cleaned_data['account_balance']
        }, None

class TransactionProcessor(DataProcessor):
    def process_row(self, row) -> Tuple[Optional[dict], Optional[str]]:
        cleaned_data, errors = validate_transaction(row)

        if errors:
            return None, '; '.join(errors)

        return {
            'transaction_id': cleaned_data['transaction_id'],
            'client_id': cleaned_data['client_id'],
            'transaction_type': cleaned_data['transaction_type'],
            'transaction_date': cleaned_data['transaction_date'],
            'amount': cleaned_data['amount'],
            'currency': cleaned_data['currency']
        }, None