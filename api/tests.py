from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from core.models import Client, Transaction
import uuid
from django.utils import timezone
from api.errors import APIErrorMessages

class APITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.token = Token.objects.create(user=self.user)

        self.client_id = str(uuid.uuid4())
        self.test_client = Client.objects.create(
            client_id=self.client_id,
            name='Test Client',
            email='testclient@example.com',
            date_of_birth='1990-01-01',
            country='Testland',
            account_balance=1000.00
        )

        self.transaction = Transaction.objects.create(
            transaction_id=str(uuid.uuid4()),
            client=self.test_client,
            transaction_type='buy',
            transaction_date=timezone.now(),
            amount=100.00,
            currency='USD'
        )

    def assertTransactionData(self, response_data, expected_transaction):
        self.assertEqual(float(response_data[0]['amount']), expected_transaction.amount)
        self.assertEqual(response_data[0]['transaction_type'], expected_transaction.transaction_type)
        self.assertEqual(response_data[0]['client'], expected_transaction.client.client_id)
        self.assertEqual(response_data[0]['currency'], expected_transaction.currency)

    def test_client_transactions_success(self):
        url = reverse('client-transactions', args=[self.client_id])
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        self.assertEqual(len(response_data), 1)
        self.assertTransactionData(response_data, self.transaction)


    def test_client_transactions_invalid_client_id(self):
        url = reverse('client-transactions', args=['invalid-client-id'])
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], APIErrorMessages.INVALID_CLIENT_ID)

    def test_client_transactions_no_transactions(self):
        new_client = Client.objects.create(
            client_id=str(uuid.uuid4()),
            name='New Client',
            email='newclient@example.com',
            date_of_birth='1990-01-01',
            country='Testland',
            account_balance=1000.00
        )
        url = reverse('client-transactions', args=[new_client.client_id])
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_login_user_success(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'testpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_user_invalid_credentials(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'wrongpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(APIErrorMessages.INVALID_CREDENTIALS, response.data['error'])

    def test_register_user_invalid_input(self):
        url = reverse('register')
        response = self.client.post(url, {'username': '', 'password': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error'])
        self.assertIn('password', response.data['error'])

    def test_client_transactions_invalid_token(self):
        url = reverse('client-transactions', args=[self.client_id])
        response = self.client.get(url, HTTP_AUTHORIZATION='Token invalid_token')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual('Invalid token.', response.data['detail'])
