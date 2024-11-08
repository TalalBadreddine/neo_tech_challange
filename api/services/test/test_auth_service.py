from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import status
from api.services.auth_service import AuthService
from api.errors import APIErrorMessages
import re

class AuthServiceTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.valid_user_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        self.test_user = User.objects.create_user(
            username='existinguser',
            password='existing123'
        )

    def test_register_success(self):
        """Test successful user registration"""
        response = AuthService.register(self.valid_user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

        self.assertTrue(re.match(r'^[a-f0-9]{40}$', response.data['token']))

        self.assertEqual(response.data['user']['username'], self.valid_user_data['username'])

        user = User.objects.get(username=self.valid_user_data['username'])
        self.assertTrue(user.check_password(self.valid_user_data['password']))

    def test_register_duplicate_username(self):
        """Test registration with existing username"""
        response = AuthService.register({
            'username': 'existinguser',
            'password': 'newpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_register_invalid_password(self):
        """Test registration with invalid password"""
        response = AuthService.register({
            'username': 'newuser',
            'password': 'short'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = AuthService.register({
            'username': 'newuser',
            'password': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_username(self):
        """Test registration with invalid username"""
        response = AuthService.register({
            'username': 'ab',
            'password': 'validpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = AuthService.register({
            'username': '',
            'password': 'validpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        """Test registration with missing fields"""
        response = AuthService.register({'username': 'testuser'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = AuthService.register({'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = AuthService.register({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test successful login"""
        response = AuthService.login({
            'username': 'existinguser',
            'password': 'existing123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

        self.assertTrue(re.match(r'^[a-f0-9]{40}$', response.data['token']))

        self.assertEqual(response.data['user']['username'], 'existinguser')

    def test_login_wrong_password(self):
        """Test login with wrong password"""
        response = AuthService.login({
            'username': 'existinguser',
            'password': 'wrongpass'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], APIErrorMessages.INVALID_CREDENTIALS)

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = AuthService.login({
            'username': 'nonexistentuser',
            'password': 'somepass123'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], APIErrorMessages.INVALID_CREDENTIALS)

    def test_login_invalid_data(self):
        """Test login with invalid data"""
        response = AuthService.login({})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = AuthService.login({'username': 'existinguser'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = AuthService.login({'password': 'existing123'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_uniqueness(self):
        """Test token uniqueness for multiple logins"""
        response1 = AuthService.login({
            'username': 'existinguser',
            'password': 'existing123'
        })
        token1 = response1.data['token']

        response2 = AuthService.login({
            'username': 'existinguser',
            'password': 'existing123'
        })
        token2 = response2.data['token']

        self.assertEqual(token1, token2)

    def test_password_hashing(self):
        """Test that passwords are properly hashed"""
        response = AuthService.register(self.valid_user_data)
        user = User.objects.get(username=self.valid_user_data['username'])

        self.assertNotEqual(user.password, self.valid_user_data['password'])
        self.assertTrue(user.check_password(self.valid_user_data['password']))

    def test_token_creation(self):
        """Test token creation behavior"""
        response = AuthService.register(self.valid_user_data)
        first_token = response.data['token']

        Token.objects.all().delete()

        response = AuthService.login(self.valid_user_data)
        new_token = response.data['token']

        self.assertNotEqual(first_token, new_token)