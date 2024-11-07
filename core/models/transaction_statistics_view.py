from pickle import TRUE
from django.db import models

class TransactionStatistics(models.Model):
    client_id = models.IntegerField(primary_key=True)
    total_transactions = models.IntegerField()
    total_spent = models.DecimalField(max_digits=25, decimal_places=2)
    total_gained = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'transaction_statistics'

    @classmethod
    def refresh(cls):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW transaction_statistics")

    def __str__(self):
        return f"Client ID: {self.client_id}, Total transactions: {self.total_transactions}, Total spent: {self.total_spent}, Total gained: {self.total_gained}"
