from rest_framework import serializers
from core.models.transaction import Transaction
from datetime import datetime
from django.contrib.auth.models import User

class TansactionQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
            start_date = attrs.get('start_date')
            end_date = attrs.get('end_date')

            if start_date:
                try:
                    datetime.strptime(str(start_date), '%Y-%m-%d')
                except ValueError:
                    raise serializers.ValidationError({"start_date": "Invalid date format. Please use YYYY-MM-DD."})

            if end_date:
                try:
                    datetime.strptime(str(end_date), '%Y-%m-%d')
                except ValueError:
                    raise serializers.ValidationError({"end_date": "Invalid date format. Please use YYYY-MM-DD."})


            if start_date and end_date:
                if start_date > end_date:
                    raise serializers.ValidationError("start_date must be before end_date.")

            return attrs


class TransactionListSerializer(serializers.ModelSerializer):
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


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(min_length=3)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta(object):
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
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
            raise serializers.ValidationError("A user with this username already exists.")

        password = attrs.get('password')
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        return attrs

    def validate_login(self, attrs):
        username = attrs.get('username')
        if not User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Invalid username or password.")

        password = attrs.get('password')
        user = User.objects.filter(username=username).first()
        if user and not user.check_password(password):
            raise serializers.ValidationError("Invalid username or password.")

        return attrs