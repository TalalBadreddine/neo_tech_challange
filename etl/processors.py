from typing import Optional, Protocol
import pandas as pd
from .validators import ClientData, TransactionData

class DataProcessor(Protocol):
    def process_row(self, row) -> Optional[dict]:
        pass

class ClientProcessor:

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return (df
            .dropna(subset=['client_id', 'name', 'email'])
            .assign(
                email=lambda x: x['email'].str.lower().str.strip(),
                name=lambda x: x['name'].str.strip(),
                country=lambda x: x['country'].str.upper().str.strip(),
                account_balance=lambda x: pd.to_numeric(x['account_balance'], errors='coerce').fillna(0)
            ))

    def process_row(self, row) -> Optional[dict]:
        try:
            client_data = ClientData.from_row(row)
            return {
                'client_id': client_data.client_id,
                'defaults': {
                    'name': client_data.name,
                    'email': client_data.email,
                    'date_of_birth': client_data.date_of_birth,
                    'country': client_data.country,
                    'account_balance': client_data.account_balance
                }
            }
        except (ValueError) as e:
            return None

class TransactionProcessor:

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return (df
            .dropna(subset=['transaction_id', 'client_id', 'amount'])
            .assign(
                transaction_type=lambda x: x['transaction_type'].str.upper().str.strip(),
                currency=lambda x: x['currency'].str.upper().str.strip(),
                amount=lambda x: pd.to_numeric(x['amount'], errors='coerce')
            ))

    def process_row(self, row) -> Optional[dict]:
        try:
            transaction_data = TransactionData.from_row(row)
            return {
                'transaction_id': transaction_data.transaction_id,
                'defaults': {
                    'client_id': transaction_data.client_id,
                    'transaction_type': transaction_data.transaction_type,
                    'transaction_date': transaction_data.transaction_date,
                    'amount': transaction_data.amount,
                    'currency': transaction_data.currency
                }
            }
        except (ValueError) as e:
            return None