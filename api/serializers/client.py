from core.models.client import Client
from rest_framework import serializers

class ClientQuerySerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    country = serializers.CharField(required=False)
    min_balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    max_balance = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    created_after = serializers.DateTimeField(required=False)
    created_before = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(max_value=999, required=False)

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
