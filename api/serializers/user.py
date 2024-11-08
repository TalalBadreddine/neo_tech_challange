from rest_framework import serializers
from django.contrib.auth.models import User
from api.errors import APIErrorMessages

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        min_length=3,
        max_length=150,
        help_text="Username for the account"
    )

    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        help_text="Password for the account"
    )

    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }
        swagger_schema_fields = {
            "example": {
                "username": "john_doe",
                "password": "password123",
            }
        }
    def validate(self, attrs):
        if self.context.get('is_registration'):
            return self.validate_registration(attrs)
        elif self.context.get('is_login'):
            return self.validate_login(attrs)
        return attrs

    def validate_registration(self, attrs):
        username = attrs.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(APIErrorMessages.USERNAME_EXISTS)

        password = attrs.get('password')
        if len(password) < 8:
            raise serializers.ValidationError(APIErrorMessages.PASSWORD_TOO_SHORT)

        return attrs

    def validate_login(self, attrs):
        username = attrs.get('username')
        if not User.objects.filter(username=username).exists():
            raise serializers.ValidationError(APIErrorMessages.INVALID_CREDENTIALS)

        password = attrs.get('password')
        user = User.objects.filter(username=username).first()
        if user and not user.check_password(password):
            raise serializers.ValidationError(APIErrorMessages.INVALID_CREDENTIALS)

        return attrs