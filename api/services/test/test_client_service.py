from django.test import TestCase
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from core.models.client import Client
from api.services.client_service import ClientService
from rest_framework import status
import uuid

class TestClientService(TestCase):
    def setUp(self):

        self.client1 = Client.objects.create(
            client_id=str(uuid.uuid4()),
            name="John Doe",
            email="john@example.com",
            date_of_birth="1990-01-01",
            country="USA",
            account_balance=Decimal("1000.00")
        )

        self.client2 = Client.objects.create(
            client_id=str(uuid.uuid4()),
            name="Jane Smith",
            email="jane@example.com",
            date_of_birth="1995-01-01",
            country="UK",
            account_balance=Decimal("2000.00")
        )

        self.client3 = Client.objects.create(
            client_id=str(uuid.uuid4()),
            name="John Smith",
            email="john.smith@example.com",
            date_of_birth="1985-01-01",
            country="USA",
            account_balance=Decimal("3000.00")
        )

    def test_get_clients_no_filters(self):
        """Test getting clients without any filters"""
        response = ClientService.get_clients({})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_get_clients_with_limit(self):
        """Test limit parameter"""
        response = ClientService.get_clients({'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_clients_by_name(self):
        """Test filtering by name"""
        response = ClientService.get_clients({'name': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for client in response.data:
            self.assertIn('John', client['name'])

    def test_get_clients_by_country(self):
        """Test filtering by country"""
        response = ClientService.get_clients({'country': 'USA'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for client in response.data:
            self.assertEqual(client['country'], 'USA')

    def test_get_clients_by_balance_range(self):
        """Test filtering by balance range"""
        response = ClientService.get_clients({
            'min_balance': '1500.00',
            'max_balance': '2500.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Jane Smith')

    def test_get_clients_by_creation_date(self):
        """Test filtering by creation date range"""
        now = timezone.now()
        response = ClientService.get_clients({
            'created_after': (now - timedelta(minutes=5)).isoformat(),
            'created_before': now.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_get_clients_combined_filters(self):
        """Test combining multiple filters"""
        response = ClientService.get_clients({
            'country': 'USA',
            'min_balance': '2000.00',
            'limit': 1
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'John Smith')

    def test_get_clients_invalid_params(self):
        """Test with invalid parameters"""
        response = ClientService.get_clients({
            'min_balance': 'invalid'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_clients_empty_result(self):
        """Test when no clients match the filters"""
        response = ClientService.get_clients({
            'country': 'NonExistentCountry'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_clients_email_filter(self):
        """Test filtering by email"""
        response = ClientService.get_clients({
            'email': 'john@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'john@example.com')

    def test_get_clients_max_limit(self):
        """Test maximum limit constraint"""
        response = ClientService.get_clients({
            'limit': 1000
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_clients_boundary_balance(self):
        """Test balance filtering at exact boundary values"""
        response = ClientService.get_clients({
            'min_balance': '1000.00',
            'max_balance': '1000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['account_balance'], '1000.00')

    def test_get_clients_case_sensitivity(self):
        """Test case sensitivity in string filters"""
        response = ClientService.get_clients({
            'name': 'john'  # Testing case-insensitive search
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)