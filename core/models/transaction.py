from django.db import models
from django.contrib.postgres.indexes import BTreeIndex
from .client import Client

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    transaction_id = models.CharField(max_length=50, primary_key=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            BTreeIndex(fields=['client']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.client.name} ({self.transaction_type})"
