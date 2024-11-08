from rest_framework import serializers

class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField(
        help_text="Authentication token for API requests"
    )
    user = serializers.DictField(
        help_text="User information"
    )

    class Meta:
        swagger_schema_fields = {
            "example": {
                "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                "user": {
                    "username": "john_doe"
                }
            }
        }

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(
        help_text="Error message"
    )

    class Meta:
        swagger_schema_fields = {
            "example": {
                "error": "Invalid credentials provided"
            }
        }