from api.serializers.transaction import TransactionQuerySerializer, TransactionResponseSerializer
from rest_framework.response import Response
from api.errors import APIErrorMessages
from core.models import Transaction
from rest_framework import status
from core.logging import logger
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

        logger.info("Client transactions query initiated", extra={
            'component': 'transaction_service',
            'action': 'query_start',
            'client_id': client_id,
            'query_params': query_params
        })

        try:
            uuid.UUID(client_id)
        except ValueError:
            logger.error("Invalid client ID format", extra={
                'component': 'transaction_service',
                'action': 'client_id_validation_failed',
                'client_id': client_id,
                'error': 'Invalid UUID format'
            })

            return Response(
                {'error': APIErrorMessages.INVALID_CLIENT_ID},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_serializer = TransactionQuerySerializer(data=query_params)
        if not query_serializer.is_valid():
            logger.warning("Invalid query parameters", extra={
                'component': 'transaction_service',
                'action': 'query_validation_failed',
                'client_id': client_id,
                'query_params': query_params,
                'validation_errors': query_serializer.errors
            })

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

            logger.info("Applying transaction filters", extra={
                'component': 'transaction_service',
                'action': 'applying_filters',
                'client_id': client_id,
                'filters': filters
            })

            transactions = Transaction.objects.filter(**filters)
            serializer = TransactionResponseSerializer(transactions, many=True)

            logger.info("Transaction results serialized", extra={
                'component': 'transaction_service',
                'action': 'serialization_complete',
                'client_id': client_id,
                'results_count': len(serializer.data)
            })

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:

            logger.error("Error processing transaction query", extra={
                'component': 'transaction_service',
                'action': 'query_failed',
                'client_id': client_id,
                'filters': filters if 'filters' in locals() else None,
                'error': str(e)
            })
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )