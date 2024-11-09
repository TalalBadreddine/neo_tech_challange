from typing import Optional, Tuple, List, Dict
import pandas as pd
from django.utils.timezone import make_aware
from .validators import validate_client, validate_transaction

class DataProcessor:
    def process_row(self, row) -> Tuple[Optional[dict], Optional[str]]:
        raise NotImplementedError

    def process_data(self, df: pd.DataFrame) -> Tuple[List[Dict], int, List[Dict]]:
        valid_records = []
        errors = []

        for _, row in df.iterrows():
            try:
                record, error = self.process_row(row)
                if record and not error:
                    valid_records.append(record)
                else:
                    errors.append({
                        'row': row.to_dict(),
                        'error': error or 'Processing failed'
                    })
            except Exception as e:
                errors.append({
                    'row': row.to_dict(),
                    'error': str(e)
                })

        return valid_records, len(errors), errors

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