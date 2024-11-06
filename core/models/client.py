from django.db import models
from django.contrib.postgres.indexes import BTreeIndex

class Client(models.Model):
    client_id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100)
    account_balance = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            BTreeIndex(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.client_id})"
