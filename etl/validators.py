from datetime import date, datetime
from decimal import Decimal
import pandas as pd
import re
from typing import Any, Optional
from django.utils import timezone
import pytz

class Validator:
    @staticmethod
    def validate_field(value: Any, field_type: str, **kwargs) -> tuple[Any, Optional[str]]:
        validators = {
            'email': Validator.validate_email,
            'string': Validator.validate_string,
            'date': Validator.validate_date,
            'datetime': Validator.validate_datetime,
            'decimal': Validator.validate_decimal,
            'currency': Validator.validate_currency,
            'transaction_type': Validator.validate_transaction_type
        }

        validator = validators.get(field_type)
        if not validator:
            return value, f"Unknown field type: {field_type}"

        return validator(value, **kwargs)

    @staticmethod
    def validate_email(value: str, **kwargs) -> tuple[str, Optional[str]]:
        if pd.isna(value):
            return "", "Email is required"

        email = str(value).lower().strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(pattern, email):
            return email, "Invalid email format"

        max_length = kwargs.get('max_length', 100)
        if len(email) > max_length:
            return email, f"Email exceeds maximum length of {max_length}"

        return email, None

    @staticmethod
    def validate_string(value: str, **kwargs) -> tuple[str, Optional[str]]:
        if pd.isna(value):
            return "", "String is required" if kwargs.get('required', False) else None

        cleaned = str(value).strip()
        max_length = kwargs.get('max_length')

        if max_length and len(cleaned) > max_length:
            return cleaned, f"String exceeds maximum length of {max_length}"

        return cleaned, None

    @staticmethod
    def validate_date(value: Any, **kwargs) -> tuple[Optional[date], Optional[str]]:
        if pd.isna(value):
            return None, "Date is required" if kwargs.get('required', False) else None

        try:
            parsed_date = pd.to_datetime(value, utc=False)

            return parsed_date.replace(tzinfo=None).date(), None
        except Exception as e:
            return None, f"Invalid date format: {str(e)}"

    @staticmethod
    def validate_decimal(value: Any, **kwargs) -> tuple[Decimal, Optional[str]]:
        if pd.isna(value):
            return Decimal('0'), "Decimal is required" if kwargs.get('required', False) else None

        try:
            decimal_value = Decimal(str(value))
            max_digits = kwargs.get('max_digits', 15)
            decimal_places = kwargs.get('decimal_places', 2)

            if abs(decimal_value.as_tuple().exponent) > decimal_places:
                return decimal_value, f"Value exceeds maximum decimal places of {decimal_places}"

            if len(str(decimal_value).replace('.', '')) > max_digits:
                return decimal_value, f"Value exceeds maximum digits of {max_digits}"

            min_value = kwargs.get('min_value', None)
            if min_value is not None and decimal_value < min_value:
                return decimal_value, f"Value must be greater than {min_value}"

            return decimal_value, None
        except Exception as e:
            return Decimal('0'), f"Invalid decimal format: {str(e)}"

    @staticmethod
    def validate_currency(value: str, **kwargs) -> tuple[str, Optional[str]]:
        if pd.isna(value):
            return "", "Currency is required"

        currency = str(value).upper().strip()
        length = kwargs.get('length', 3)

        if len(currency) != length:
            return currency, f"Currency must be exactly {length} characters"

        return currency, None

    @staticmethod
    def validate_datetime(value: Any, **kwargs) -> tuple[Optional[datetime], Optional[str]]:
        if pd.isna(value):
            return None, "Datetime is required" if kwargs.get('required', False) else None

        try:
            naive_date = pd.to_datetime(value)
            tz = kwargs.get('timezone', 'UTC')

            if naive_date.tzinfo is None:
                aware_date = timezone.make_aware(naive_date)
            else:
                aware_date = naive_date

            localized_date = timezone.localtime(aware_date, pytz.timezone(tz))
            return localized_date, None
        except Exception as e:
            return None, f"Invalid datetime format: {str(e)}"
    @staticmethod
    def validate_transaction_type(value: str, **kwargs) -> tuple[str, Optional[str]]:
        if pd.isna(value):
            return "", "Transaction type is required"

        trans_type = str(value).upper().strip()
        valid_types = kwargs.get('valid_types', {'BUY', 'SELL'})

        if trans_type not in valid_types:
            return trans_type, f"Invalid transaction type. Must be one of: {valid_types}"

        return trans_type, None

def _validate_data(row: dict, fields: dict) -> tuple[dict, list[str]]:
    """Base validation function that handles common validation patterns."""
    validator = Validator()
    errors = []
    cleaned_data = {}

    for field, (field_type, kwargs) in fields.items():
        if callable(kwargs):
            kwargs = kwargs(cleaned_data)

        value, error = validator.validate_field(row.get(field), field_type, **kwargs)
        if error:
            errors.append(error)
        cleaned_data[field] = value

    return cleaned_data, errors


def validate_client(row: dict) -> tuple[dict, list[str]]:
    fields = {
        'client_id': ('string', {'required': True, 'max_length': 50}),
        'name': ('string', {'required': True, 'max_length': 100}),
        'email': ('email', {'required': True, 'max_length': 100}),
        'date_of_birth': ('date', {'required': True}),
        'country': ('string', {'required': False, 'max_length': 15}),
        'account_balance': ('decimal', {'required': False, 'max_digits': 15, 'decimal_places': 2}),
    }
    return _validate_data(row, fields)

def validate_transaction(row: dict) -> tuple[dict, list[str]]:
    def get_amount_kwargs(trans_type):
        kwargs = {
            'required': True,
            'max_digits': 15,
            'decimal_places': 2,
        }
        if trans_type == 'BUY':
            kwargs['min_value'] = Decimal('0')
        elif trans_type == 'SELL':
            kwargs['max_value'] = Decimal('0')
        return kwargs

    fields = {
        'transaction_id': ('string', {'required': True, 'max_length': 50}),
        'client_id': ('string', {'required': True, 'max_length': 50}),
        'transaction_type': ('transaction_type', {'required': True, 'valid_types': {'BUY', 'SELL'}}),
        'transaction_date': ('datetime', {'required': True, 'timezone': 'UTC'}),
        'currency': ('currency', {'length': 3}),
        'amount': ('decimal', lambda d: get_amount_kwargs(d.get('transaction_type'))),
    }

    return _validate_data(row, fields)