from rest_framework.response import Response
from rest_framework import status
from core.models import Transaction
from .serializers import TansactionQuerySerializer, TransactionListSerializer, UserSerializer
from core.models.client import Client
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate

import uuid

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def client_transactions(request, client_id):
    try:
        uuid.UUID(client_id)
    except ValueError:
        return Response({'error': 'Invalid client_id'}, status=status.HTTP_400_BAD_REQUEST)

    user = Client.objects.filter(client_id=client_id).first()

    if not user:
        return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


    query_serializer = TansactionQuerySerializer(data=request.query_params)

    if not query_serializer.is_valid():
        return Response(query_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = query_serializer.validated_data

    start_date = validated_data.get('start_date')
    end_date = validated_data.get('end_date')

    try:
        filters = {'client_id': client_id}

        if start_date and end_date:
            filters['transaction_date__range'] = (start_date, end_date)
        else:
            if start_date:
                filters['transaction_date__gte'] = start_date
            if end_date:
                filters['transaction_date__lte'] = end_date

        transactions = Transaction.objects.filter(**filters)
        serializer = TransactionListSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login_user(request):
    serializer = UserSerializer(data=request.data, context={'is_login': True})

    if serializer.is_valid():
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(username=username, password=password)

        token, _ = Token.objects.get_or_create(user=user)
        serializer = UserSerializer(user)
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data, context={'is_registration': True})

    if serializer.is_valid():
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)