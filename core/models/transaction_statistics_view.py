from django.db import connection, models
from django.utils import timezone
from core.models.view import MaterializedViewRefresh


class TransactionStatistics(models.Model):
    client_id = models.CharField(max_length=50, primary_key=True)
    total_transactions = models.IntegerField()
    total_spent = models.DecimalField(max_digits=25, decimal_places=2)
    total_gained = models.DecimalField(max_digits=25, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'transaction_statistics'

    @classmethod
    def refresh(cls):
        refresh_record = MaterializedViewRefresh.objects.create(
            view_name='transaction_statistics',
            started_at=timezone.now()
        )
        try:
            start_time = timezone.now()
            with connection.cursor() as cursor:
                cursor.execute("REFRESH MATERIALIZED VIEW transaction_statistics")

            duration = (timezone.now() - start_time).total_seconds()

            refresh_record.completed_at = timezone.now()
            refresh_record.success = True
            refresh_record.duration_seconds = duration
            refresh_record.save()

        except Exception as e:
            refresh_record.completed_at = timezone.now()
            refresh_record.success = False
            refresh_record.error_message = str(e)
            refresh_record.save()
            raise e

    def __str__(self):
        return f"Client ID: {self.client_id}, Total transactions: {self.total_transactions}, Total spent: {self.total_spent}, Total gained: {self.total_gained}"
