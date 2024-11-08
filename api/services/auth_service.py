from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from api.errors import APIErrorMessages
from api.serializers import UserSerializer

class AuthService:
    @staticmethod
    def login(data):
        """
        Authenticate and login a user.

        Parameters:
        - data: Dict
            - username: String (min length: 3)
            - password: String (min length: 8)

        Returns:
        - Response object with token and user data or error
        """
        serializer = UserSerializer(data=data, context={'is_login': True})

        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')

            user = authenticate(username=username, password=password)

            token, _ = Token.objects.get_or_create(user=user)
            response_data = {
                'token': token.key,
                'user': UserSerializer(user).data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {'error': APIErrorMessages.INVALID_CREDENTIALS},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def register(data):
        """
        Register a new user account.

        Parameters:
        - data: Dict
            - username: String (min length: 3)
            - password: String (min length: 8)

        Returns:
        - Response object with token and user data or error
        """
        serializer = UserSerializer(data=data, context={'is_registration': True})

        if serializer.is_valid():
            user = serializer.save()
            user.set_password(serializer.validated_data['password'])
            user.save()

            token = Token.objects.create(user=user)
            response_data = {
                'token': token.key,
                'user': serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )