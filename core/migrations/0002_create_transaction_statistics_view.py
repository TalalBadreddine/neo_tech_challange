from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    sql = """
        CREATE MATERIALIZED VIEW transaction_statistics AS
        SELECT
            t.client_id,
            COUNT(*) as total_transactions,
            SUM(CASE
                WHEN transaction_type = 'BUY' THEN amount
                ELSE 0
            END) as total_spent,
            SUM(CASE
                WHEN transaction_type = 'SELL' THEN ABS(amount)
                ELSE 0
            END) as total_gained
        FROM core_transaction t
        GROUP BY t.client_id;

        CREATE UNIQUE INDEX transaction_statistics_client_id_idx
        ON transaction_statistics (client_id);
    """

    reverse_sql = """
        DROP MATERIALIZED VIEW IF EXISTS transaction_statistics CASCADE;
        DROP INDEX IF EXISTS transaction_statistics_client_id_idx;
    """

    operations = [
        migrations.RunSQL(sql=sql, reverse_sql=reverse_sql)
    ]