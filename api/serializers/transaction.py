from rest_framework import serializers
from core.models.transaction import Transaction

class TransactionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'transaction_id',
            'client',
            'transaction_type',
            'transaction_date',
            'amount',
            'currency',
            'created_at',
        ]
        swagger_schema_fields = {
            "example": {
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
                "client": "98765432-e89b-12d3-a456-426614174000",
                "transaction_type": "DEPOSIT",
                "transaction_date": "2024-01-15",
                "amount": "1250.50",
                "currency": "USD",
                "created_at": "2024-01-15T14:30:00Z"
            }
        }

class TransactionQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(
        required=False,
        help_text="Start date for filtering transactions"
    )
    end_date = serializers.DateField(
        required=False,
        help_text="End date for filtering transactions"
    )

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                "Start date must be before end date"
            )
        return attrs