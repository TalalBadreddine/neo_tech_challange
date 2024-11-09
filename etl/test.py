from django.test import TestCase
import uuid
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from core.models import Client, Transaction
from core.models.etl_job import ETLJob
from core.models.transaction_statistics_view import TransactionStatistics
from etl.tasks import process_clients_file, process_transactions_file
import tempfile
import os
import shutil

class ETLProcessTest(TestCase):
    def setUp(self):
        """Set up test data and files"""
        self.temp_dir = tempfile.mkdtemp()


        self.client_1_id = str(uuid.uuid4())
        self.client_2_id = str(uuid.uuid4())
        self.transaction_1_id = str(uuid.uuid4())
        self.transaction_2_id = str(uuid.uuid4())


        self.client_data = [
            {
                'client_id': self.client_1_id,
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'date_of_birth': '1990-01-01',
                'country': 'US',
                'account_balance': '1000.50'
            },
            {
                'client_id': self.client_2_id,
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'date_of_birth': '1985-06-15',
                'country': 'UK',
                'account_balance': '2500.75'
            },

            {
                'client_id': 'not-a-uuid',
                'name': '',
                'email': 'invalid@email',
                'date_of_birth': 'not-a-date',
                'country': 'COUNTRY_NAME_TOO_LONG',
                'account_balance': 'not-a-number'
            }
        ]


        self.transaction_data = [
            {
                'transaction_id': self.transaction_1_id,
                'client_id': self.client_1_id,
                'transaction_type': 'BUY',
                'transaction_date': '2024-01-01 12:00:00',
                'amount': '500.00',
                'currency': 'USD'
            },
            {
                'transaction_id': self.transaction_2_id,
                'client_id': self.client_1_id,
                'transaction_type': 'SELL',
                'transaction_date': '2024-01-02 13:00:00',
                'amount': '-250.25',
                'currency': 'EUR'
            }
        ]


        self.clients_file = os.path.join(self.temp_dir, 'clients.csv')
        self.transactions_file = os.path.join(self.temp_dir, 'transactions.xlsx')


        pd.DataFrame(self.client_data).to_csv(self.clients_file, index=False)
        pd.DataFrame(self.transaction_data).to_excel(self.transactions_file, index=False)

    def tearDown(self):
        """Clean up test files"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_client_csv_processing(self):
        """Test processing of client CSV file"""
        result = process_clients_file(self.clients_file)

        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 2)
        self.assertEqual(result['failed_count'], 1)

        self.assertEqual(Client.objects.count(), 2)
        client = Client.objects.get(client_id=self.client_1_id)
        self.assertEqual(client.name, 'John Doe')
        self.assertEqual(client.account_balance, Decimal('1000.50'))

    def test_transaction_xlsx_processing(self):
        """Test processing of transaction XLSX file"""
        Client.objects.create(
            client_id=self.client_1_id,
            name='John Doe',
            email='john.doe@example.com',
            date_of_birth='1990-01-01',
            account_balance=Decimal('1000.50')
        )

        result = process_transactions_file(self.transactions_file)

        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 2)

        buy_tx = Transaction.objects.get(transaction_id=self.transaction_1_id)
        sell_tx = Transaction.objects.get(transaction_id=self.transaction_2_id)

        self.assertEqual(buy_tx.transaction_type, 'BUY')
        self.assertEqual(buy_tx.amount, Decimal('500.00'))
        self.assertEqual(sell_tx.transaction_type, 'SELL')
        self.assertEqual(sell_tx.amount, Decimal('-250.25'))

    def test_transaction_without_client(self):
        """Test transaction processing without existing client"""
        result = process_transactions_file(self.transactions_file)

        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_duplicate_client_handling(self):
        """Test handling of duplicate client records"""
        process_clients_file(self.clients_file)
        initial_count = Client.objects.count()

        result = process_clients_file(self.clients_file)

        self.assertEqual(Client.objects.count(), initial_count)
        self.assertTrue(result['success'])

    def test_large_dataset_processing(self):
        """Test processing of large dataset"""
        large_data = []
        for i in range(10000):
            large_data.append({
                'client_id': str(uuid.uuid4()),
                'name': f'Test User {i}',
                'email': f'user{i}@example.com',
                'date_of_birth': '1990-01-01',
                'country': 'US',
                'account_balance': '1000.50'
            })

        large_file = os.path.join(self.temp_dir, 'large_dataset.csv')
        pd.DataFrame(large_data).to_csv(large_file, index=False)

        result = process_clients_file(large_file, chunk_size=1000)
        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 10000)

    @patch('etl.tasks.TransactionStatistics')
    def test_statistics_refresh(self, mock_stats):
        """Test statistics refresh after transaction processing"""
        Client.objects.create(
            client_id=self.client_1_id,
            name='John Doe',
            email='john.doe@example.com',
            date_of_birth='1990-01-01',
            account_balance=Decimal('1000.50')
        )

        process_transactions_file(self.transactions_file)
        mock_stats.refresh.assert_called_once()

    def test_timezone_handling(self):
        """Test proper timezone handling in transactions"""
        from datetime import timezone

        Client.objects.create(
            client_id=self.client_1_id,
            name='John Doe',
            email='john.doe@example.com',
            date_of_birth='1990-01-01',
            account_balance=Decimal('1000.50')
        )

        process_transactions_file(self.transactions_file)

        transaction = Transaction.objects.first()
        self.assertEqual(transaction.transaction_date.tzinfo, timezone.utc)

    def test_etl_job_tracking(self):
        """Test ETL job status tracking"""
        process_clients_file(self.clients_file)

        job = ETLJob.objects.last()
        self.assertEqual(job.status, 'completed')
        self.assertTrue(job.records_processed > 0)
        self.assertIsNotNone(job.completed_at)
        self.assertIsNone(job.error_message)

    def test_failed_etl_job_tracking(self):
        """Test ETL job tracking for failed jobs"""
        result = process_clients_file("nonexistent_file.csv")

        self.assertFalse(result['success'])
        job = ETLJob.objects.last()
        self.assertEqual(job.status, 'failed')
        self.assertIsNotNone(job.error_message)

    def test_invalid_file_format(self):
        """Test handling of invalid file formats"""

        invalid_file = os.path.join(self.temp_dir, 'invalid.txt')
        with open(invalid_file, 'w') as f:
            f.write("This is not a CSV or XLSX file")

        result = process_clients_file(invalid_file)
        self.assertFalse(result['success'])
        self.assertIn('format', result.get('error', '').lower())

    def test_corrupted_file_handling(self):
        """Test handling of corrupted files"""

        corrupted_file = os.path.join(self.temp_dir, 'corrupted.xlsx')
        with open(corrupted_file, 'wb') as f:
            f.write(b'corrupted content')

        result = process_transactions_file(corrupted_file)
        self.assertFalse(result['success'])

    def test_empty_file_handling(self):
        """Test handling of empty files"""
        empty_file = os.path.join(self.temp_dir, 'empty.csv')
        pd.DataFrame([]).to_csv(empty_file, index=False)

        result = process_clients_file(empty_file)
        self.assertFalse(result['success'])

    def test_invalid_transaction_types(self):
        """Test handling of invalid transaction types"""
        invalid_transaction = {
            'transaction_id': str(uuid.uuid4()),
            'client_id': self.client_1_id,
            'transaction_type': 'INVALID_TYPE',
            'transaction_date': '2024-01-01 12:00:00',
            'amount': '500.00',
            'currency': 'USD'
        }

        file_path = os.path.join(self.temp_dir, 'invalid_transactions.xlsx')
        pd.DataFrame([invalid_transaction]).to_excel(file_path, index=False)

        result = process_transactions_file(file_path)
        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 0)
        self.assertEqual(result['failed_count'], 1)

    def test_concurrent_file_processing(self):
        """Test handling of concurrent file processing"""
        with patch('etl.tasks.process_file') as mock_process:
            process_clients_file(self.clients_file)
            process_clients_file(self.clients_file)
            self.assertEqual(mock_process.call_count, 2)

    def test_invalid_currency_handling(self):
        """Test handling of invalid currency codes"""
        invalid_transaction = {
            'transaction_id': str(uuid.uuid4()),
            'client_id': self.client_1_id,
            'transaction_type': 'BUY',
            'transaction_date': '2024-01-01 12:00:00',
            'amount': '500.00',
            'currency': 'INVALID'
        }

        file_path = os.path.join(self.temp_dir, 'invalid_currency.xlsx')
        pd.DataFrame([invalid_transaction]).to_excel(file_path, index=False)

        result = process_transactions_file(file_path)
        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 0)
        self.assertEqual(result['failed_count'], 1)

    def test_memory_usage_large_files(self):
        """Test memory usage with very large files"""
        very_large_data = []
        for i in range(100000):
            very_large_data.append({
                'client_id': str(uuid.uuid4()),
                'name': f'Test User {i}',
                'email': f'user{i}@example.com',
                'date_of_birth': '1990-01-01',
                'country': 'US',
                'account_balance': '1000.50'
            })

        file_path = os.path.join(self.temp_dir, 'very_large.csv')
        pd.DataFrame(very_large_data).to_csv(file_path, index=False)

        with patch('etl.tasks.pd.read_csv') as mock_read:
            mock_read.return_value = pd.DataFrame(very_large_data)
            result = process_clients_file(file_path, chunk_size=5000)
            self.assertTrue(result['success'])
            self.assertEqual(result['processed_count'], 100000)

    def test_end_to_end_workflow(self):
        """Test complete workflow from client creation to transaction processing"""

        client_result = process_clients_file(self.clients_file)
        self.assertTrue(client_result['success'])

        tx_result = process_transactions_file(self.transactions_file)
        self.assertTrue(tx_result['success'])

        client = Client.objects.get(client_id=self.client_1_id)
        transactions = Transaction.objects.filter(client_id=self.client_1_id)
        stats = TransactionStatistics.objects.get(client_id=self.client_1_id)

        self.assertEqual(len(transactions), 2)
        self.assertEqual(stats.total_spent, Decimal('500.00'))
        self.assertEqual(stats.total_gained, Decimal('250.25'))

    def test_performance_benchmarks(self):
        """Test performance meets requirements"""
        import time

        start_time = time.time()
        result = process_clients_file(self.clients_file)
        processing_time = time.time() - start_time

        self.assertTrue(processing_time < 5.0)
        self.assertTrue(result['processed_count'] / processing_time > 100)