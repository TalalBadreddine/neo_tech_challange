from api.serializers.client import ClientQuerySerializer, ClientSerializer
from rest_framework.response import Response
from rest_framework import status
from core.models.client import Client
from api.errors import APIErrorMessages

class ClientService:
    @staticmethod
    def get_clients(query_params):
        """
        Get all clients with filters

        Returns:
        - List of clients
        """
        try:
            serializer = ClientQuerySerializer(data=query_params)
            serializer.is_valid(raise_exception=True)
            validated_params = serializer.validated_data
        except Exception as e:
            return Response(APIErrorMessages.INVALID_QUERY_PARAMS, status=status.HTTP_400_BAD_REQUEST)

        limit = validated_params.pop('limit', 10)
        min_balance = validated_params.pop('min_balance', None)
        max_balance = validated_params.pop('max_balance', None)
        created_after = validated_params.pop('created_after', None)
        created_before = validated_params.pop('created_before', None)

        try:
            filter_conditions = {}

            filter_conditions.update(validated_params)

            if min_balance is not None:
                filter_conditions['account_balance__gte'] = min_balance
            if max_balance is not None:
                filter_conditions['account_balance__lte'] = max_balance
            if created_after is not None:
                filter_conditions['created_at__gte'] = created_after
            if created_before is not None:
                filter_conditions['created_at__lte'] = created_before

            clients = Client.objects.filter(**filter_conditions)[:limit]

            serializer = ClientSerializer(clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(APIErrorMessages.INTERNAL_SERVER_ERROR, status=status.HTTP_500_INTERNAL_SERVER_ERROR)