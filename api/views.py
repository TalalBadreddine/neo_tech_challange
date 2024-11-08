from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from api.serializers import UserSerializer, TokenResponseSerializer, ErrorResponseSerializer
from api.serializers.transaction import TransactionResponseSerializer
from api.services.transaction_service import TransactionService
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from api.services.auth_service import AuthService
from drf_yasg.utils import swagger_auto_schema
from core.throttle import CustomRateThrottle
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={
        200: TokenResponseSerializer,
        401: ErrorResponseSerializer,
    },
    operation_description="Login endpoint for users."
)
@api_view(['POST'])
def login_user(request):
    """
    Authenticate and login a user.
    [... rest of docstring ...]
    """
    return AuthService.login(request.data)

@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={
        201: TokenResponseSerializer,
        400: ErrorResponseSerializer,
    },
    operation_description="Register new user endpoint."
)
@api_view(['POST'])
@throttle_classes([CustomRateThrottle])
def register_user(request):
    """
    Register a new user account.
    """
    return AuthService.register(request.data)



@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="Token for authentication. Format: 'Token <your_token_here>'",
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'start_date',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description="Start date (YYYY-MM-DD)",
            required=False
        ),
        openapi.Parameter(
            'end_date',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            description="End date (YYYY-MM-DD)",
            required=False
        ),
    ],
    responses={
        200: TransactionResponseSerializer(many=True),
        400: ErrorResponseSerializer,
        401: 'Unauthorized',
        404: ErrorResponseSerializer,
    },
    operation_description="Get transactions for a specific client with optional date filtering."
)
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@throttle_classes([CustomRateThrottle])
def client_transactions(request, client_id):
    """
    Get client transactions with optional date filtering.
    """
    return TransactionService.get_client_transactions(client_id, request.query_params)