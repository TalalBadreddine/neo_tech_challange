from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from api.errors import APIErrorMessages
from api.serializers import UserSerializer
from core.logging import logger

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
        logger.info("Login attempt", extra={
            'component': 'auth_service',
            'action': 'login_attempt',
            'username': data.get('username')
        })

        serializer = UserSerializer(data=data, context={'is_login': True})

        if not serializer.is_valid():
            logger.warning("Login validation failed", extra={
                'component': 'auth_service',
                'action': 'login_validation_failed',
                'username': data.get('username'),
                'errors': serializer.errors
            })
            return Response(
                {'error': APIErrorMessages.INVALID_CREDENTIALS},
                status=status.HTTP_401_UNAUTHORIZED
            )

        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            logger.warning("Authentication failed", extra={
                'component': 'auth_service',
                'action': 'authentication_failed',
                'username': username
            })
            return Response(
                {'error': APIErrorMessages.INVALID_CREDENTIALS},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, created = Token.objects.get_or_create(user=user)

        logger.info("Login successful", extra={
            'component': 'auth_service',
            'action': 'login_success',
            'user_id': user.id,
            'username': username,
            'token_created': created
        })

        response_data = {
            'token': token.key,
            'user': UserSerializer(user).data
        }
        return Response(response_data, status=status.HTTP_200_OK)

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
        logger.info("Registration attempt", extra={
            'component': 'auth_service',
            'action': 'register_attempt',
            'username': data.get('username')
        })

        serializer = UserSerializer(data=data, context={'is_registration': True})

        if not serializer.is_valid():
            logger.warning("Registration validation failed", extra={
                'component': 'auth_service',
                'action': 'register_validation_failed',
                'username': data.get('username'),
                'errors': serializer.errors
            })
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save()
            user.set_password(serializer.validated_data['password'])
            user.save()

            token = Token.objects.create(user=user)

            logger.info("Registration successful", extra={
                'component': 'auth_service',
                'action': 'register_success',
                'user_id': user.id,
                'username': user.username
            })

            response_data = {
                'token': token.key,
                'user': serializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("Registration failed", extra={
                'component': 'auth_service',
                'action': 'register_error',
                'username': data.get('username'),
                'error': str(e)
            })
            return Response(
                {'error': APIErrorMessages.INTERNAL_SERVER_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )