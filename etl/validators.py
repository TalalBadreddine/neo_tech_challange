from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import pandas as pd
import re
from django.utils import timezone

class DataUtil:
    @staticmethod
    def clean_string(value, max_length=None) -> str:
        if pd.isna(value):
            return ""
        cleaned = str(value).strip()
        if max_length and len(cleaned) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        return cleaned

    @staticmethod
    def clean_decimal(value, max_digits=15, decimal_places=2) -> Decimal:
        if pd.isna(value):
            return Decimal('0')
        decimal_value = Decimal(str(value))

        if abs(decimal_value.as_tuple().exponent) > decimal_places:
            raise ValueError(f"Value exceeds maximum decimal places of {decimal_places}")

        if len(str(decimal_value).replace('.', '')) > max_digits:
            raise ValueError(f"Value exceeds maximum digits of {max_digits}")
        return decimal_value

    @staticmethod
    def is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


@dataclass
class ClientData(DataUtil):
    client_id: str
    name: str
    email: str
    date_of_birth: date
    country: str
    account_balance: Decimal

    VALID_COUNTRY_LENGTH = 100

    @classmethod
    def from_row(cls, row):

        client_id = cls.clean_string(row['client_id'], max_length=50)
        if not client_id:
            raise ValueError("Client ID is required")


        name = cls.clean_string(row['name'], max_length=255)
        if not name:
            raise ValueError("Name is required")


        email = cls.clean_string(row['email'], max_length=254).lower()
        if not cls.is_valid_email(email):
            raise ValueError(f"Invalid email format: {email}")


        country = cls.clean_string(row['country'], max_length=cls.VALID_COUNTRY_LENGTH).upper()
        if not country:
            raise ValueError("Country is required")

        return cls(
            client_id=client_id,
            name=name,
            email=email,
            date_of_birth=pd.to_datetime(row['date_of_birth']).date(),
            country=country,
            account_balance=cls.clean_decimal(row['account_balance'], max_digits=15, decimal_places=2)
        )


@dataclass
class TransactionData(DataUtil):
    transaction_id: str
    client_id: str
    transaction_type: str
    transaction_date: date
    amount: Decimal
    currency: str

    VALID_TRANSACTION_TYPES = {'BUY', 'SELL'}
    CURRENCY_LENGTH = 3

    @classmethod
    def from_row(cls, row):

        transaction_id = cls.clean_string(row['transaction_id'], max_length=50)
        if not transaction_id:
            raise ValueError("Transaction ID is required")


        client_id = cls.clean_string(row['client_id'], max_length=50)
        if not client_id:
            raise ValueError("Client ID is required")


        transaction_type = cls.clean_string(row['transaction_type'], max_length=4).upper()
        if transaction_type not in cls.VALID_TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type. Must be one of: {cls.VALID_TRANSACTION_TYPES}")


        currency = cls.clean_string(row['currency'], max_length=cls.CURRENCY_LENGTH).upper()
        if not currency or len(currency) != cls.CURRENCY_LENGTH:
            raise ValueError(f"Currency must be exactly {cls.CURRENCY_LENGTH} characters")

        naive_date = pd.to_datetime(row['transaction_date'])
        aware_date = timezone.make_aware(naive_date)

        return cls(
            transaction_id=transaction_id,
            client_id=client_id,
            transaction_type=transaction_type,
            transaction_date=aware_date,
            amount=cls.clean_decimal(row['amount'], max_digits=15, decimal_places=2),
            currency=currency
        )