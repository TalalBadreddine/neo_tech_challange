from api.serializers.client import ClientQuerySerializer, ClientSerializer
from rest_framework.response import Response
from rest_framework import status
from core.models.client import Client
from api.errors import APIErrorMessages
from core.logging import logger

class ClientService:
    @staticmethod
    def get_clients(query_params):
        """
        Get all clients with filters

        Returns:
        - List of clients
        """
        logger.info("Client query initiated", extra={
            'component': 'client_service',
            'action': 'query_start',
            'query_params': query_params
        })

        try:
            serializer = ClientQuerySerializer(data=query_params)
            serializer.is_valid(raise_exception=True)
            validated_params = serializer.validated_data
        except Exception as e:
            return Response(APIErrorMessages.INVALID_QUERY_PARAMS, status=status.HTTP_400_BAD_REQUEST)

        limit = validated_params.pop('limit', 10)
        name = validated_params.pop('name', None)
        email = validated_params.pop('email', None)
        min_balance = validated_params.pop('min_balance', None)
        max_balance = validated_params.pop('max_balance', None)
        created_after = validated_params.pop('created_after', None)
        created_before = validated_params.pop('created_before', None)

        try:
            filter_conditions = {
                'name__icontains': name,
                'email__icontains': email,
                'account_balance__gte': min_balance,
                'account_balance__lte': max_balance,
                'created_at__gte': created_after,
                'created_at__lte': created_before,
                **validated_params
            }

            filter_conditions = {k: v for k, v in filter_conditions.items() if v is not None}

            clients = Client.objects.filter(**filter_conditions)[:limit]

            serializer = ClientSerializer(clients, many=True)

            logger.info("Results serialized", extra={
                'component': 'client_service',
                'action': 'serialization_complete',
                'results_count': len(clients)
            })

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing client query", extra={
                'component': 'client_service',
                'action': 'query_failed',
                'filters': filter_conditions if 'filter_conditions' in locals() else None,
                'error': str(e)
            })
            return Response(APIErrorMessages.INTERNAL_SERVER_ERROR, status=status.HTTP_500_INTERNAL_SERVER_ERROR)