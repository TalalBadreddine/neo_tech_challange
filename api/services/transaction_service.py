from api.serializers.transaction import TransactionQuerySerializer, TransactionResponseSerializer
from rest_framework.response import Response
from api.errors import APIErrorMessages
from core.models import Transaction
from rest_framework import status
import uuid

class TransactionService:
    @staticmethod
    def get_client_transactions(client_id, query_params):
        """
        Get transactions for a specific client with optional date filtering.

        Parameters:
        - client_id: UUID
            The unique identifier of the client
        - query_params: Dict
            - start_date: Date (optional)
            - end_date: Date (optional)

        Returns:
        - Response object with transactions or error
        """
        try:
            uuid.UUID(client_id)
        except ValueError:
            return Response(
                {'error': APIErrorMessages.INVALID_CLIENT_ID},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_serializer = TransactionQuerySerializer(data=query_params)
        if not query_serializer.is_valid():
            return Response(
                {'error': query_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            filters = {'client_id': client_id}
            if start_date := query_serializer.validated_data.get('start_date'):
                filters['transaction_date__gte'] = start_date
            if end_date := query_serializer.validated_data.get('end_date'):
                filters['transaction_date__lte'] = end_date

            transactions = Transaction.objects.filter(**filters)
            serializer = TransactionResponseSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )