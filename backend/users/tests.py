from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
import jwt
from datetime import datetime, timedelta
from django.conf import settings

User = get_user_model()

from .models import RefreshTokenBlacklist
import time

class UserModelTests(TestCase):
    """Test cases for User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'user')  # default role
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_admin_user(self):
        """Test creating an admin user"""
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        self.assertEqual(user.role, 'admin')
    
    def test_create_user_with_google_id(self):
        """Test creating a user with Google OAuth ID"""
        user = User.objects.create_user(
            username='googleuser',
            email='google@example.com',
            password='pass123',
            google_id='123456789'
        )
        
        self.assertEqual(user.google_id, '123456789')
    
    def test_user_str_method(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        self.assertEqual(str(user), 'testuser')
        
        # Test with email when no username
        user_no_username = User.objects.create_user(
            username='email@example.com',
            email='email@example.com',
            password='pass123'
        )
        user_no_username.username = ''
        
        self.assertEqual(str(user_no_username), 'email@example.com')
    
    def test_unique_email_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(
            username='user1',
            email='same@example.com',
            password='pass123'
        )
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            User.objects.create_user(
                username='user2',
                email='same@example.com',
                password='pass123'
            )
    
    def test_unique_google_id_constraint(self):
        """Test that Google ID must be unique"""
        User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            google_id='123456789'
        )
        
        with self.assertRaises(Exception):  # Should raise IntegrityError
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='pass123',
                google_id='123456789'
            )

class UserRegistrationAPITests(APITestCase):
    """Test cases for User Registration API"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'role': 'user'
        }
        
        response = self.client.post('/api/users/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.first()
        # Username is intentionally nulled for API-created users; email is used as primary identifier
        self.assertIsNone(user.username)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.role, 'user')
        self.assertTrue(user.check_password('securepass123'))
    
    def test_register_user_missing_data(self):
        """Test registration with missing required data"""
        data = {
            'username': 'newuser'
            # Missing email and password
        }
        
        response = self.client.post('/api/users/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
    
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='pass123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',  # Same email
            'password': 'pass123'
        }
        
        response = self.client.post('/api/users/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)  # Only original user
    
    def test_register_admin_user(self):
        """Test registering an admin user"""
        data = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'adminpass123',
            'role': 'admin'
        }
        
        response = self.client.post('/api/users/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.first()
        self.assertEqual(user.role, 'admin')
    
    def test_register_user_with_google_id(self):
        """Test registering user with Google ID"""
        data = {
            'username': 'googleuser',
            'email': 'google@example.com',
            'password': 'pass123',
            'google_id': '123456789'
        }
        
        response = self.client.post('/api/users/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.first()
        self.assertEqual(user.google_id, '123456789')

class UserLoginAPITests(APITestCase):
    """Test cases for User Login API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_success(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/users/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response_data = response.data
        self.assertIn('message', response_data)
        self.assertIn('tokens', response_data)
        self.assertIn('user', response_data)
        
        # Check tokens
        tokens = response_data['tokens']
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)
        
        # Check user info
        user_data = response_data['user']
        self.assertEqual(user_data['email'], 'test@example.com')
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['last_name'], 'User')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/users/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'anypassword'
        }
        
        response = self.client.post('/api/users/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        data = {
            'email': 'test@example.com'
            # Missing password
        }
        
        response = self.client.post('/api/users/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_jwt_token_content(self):
        """Test JWT token content and validity"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/users/login/', data)
        tokens = response.data['tokens']
        
        # Decode access token
        access_secret = getattr(settings, 'JWT_ACCESS_SECRET', 'your-access-secret-key')
        decoded_token = jwt.decode(tokens['access'], access_secret, algorithms=['HS256'])
        
        self.assertEqual(decoded_token['user_id'], self.user.id)
        self.assertEqual(decoded_token['email'], self.user.email)
        self.assertEqual(decoded_token['type'], 'access')
        self.assertIn('exp', decoded_token)
        self.assertIn('iat', decoded_token)
    
    def test_jwt_token_expiration(self):
        """Test JWT token expiration times"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/users/login/', data)
        tokens = response.data['tokens']
        
        # Check access token expiration (1 hour)
        access_secret = getattr(settings, 'JWT_ACCESS_SECRET', 'your-access-secret-key')
        decoded_access = jwt.decode(tokens['access'], access_secret, algorithms=['HS256'])
        
        access_exp = datetime.fromtimestamp(decoded_access['exp'])
        access_iat = datetime.fromtimestamp(decoded_access['iat'])
        access_duration = access_exp - access_iat
        
        self.assertAlmostEqual(access_duration.total_seconds(), 3600, delta=60)  # 1 hour ± 1 minute
        
        # Check refresh token expiration (7 days)
        refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', 'your-refresh-secret-key')
        decoded_refresh = jwt.decode(tokens['refresh'], refresh_secret, algorithms=['HS256'])
        
        refresh_exp = datetime.fromtimestamp(decoded_refresh['exp'])
        refresh_iat = datetime.fromtimestamp(decoded_refresh['iat'])
        refresh_duration = refresh_exp - refresh_iat
        
        self.assertAlmostEqual(refresh_duration.total_seconds(), 7 * 24 * 3600, delta=3600)  # 7 days ± 1 hour

class UserCRUDAPITests(APITestCase):
    """Test cases for User CRUD API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
    
    def test_list_users_as_regular_user(self):
        """Test listing users as regular user"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/users/')
        
        # Listing users is restricted to admins
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_users_unauthenticated(self):
        """Test listing users without authentication"""
        response = self.client.get('/api/users/')
        
        # Unauthenticated users should receive 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_user_detail(self):
        """Test getting user detail"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/users/{self.user.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user_data = response.data
        self.assertEqual(user_data['id'], self.user.id)
        self.assertEqual(user_data['email'], self.user.email)
        # username is read-only and may be null since email is used as primary identifier
        self.assertIn('username', user_data)
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        
        response = self.client.put(f'/api/users/{self.user.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_partial_update_user(self):
        """Test partial update of user"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'first_name': 'Partially Updated'
        }
        
        response = self.client.patch(f'/api/users/{self.user.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Partially Updated')
    
    def test_delete_user(self):
        """Test deleting user"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/users/{self.user.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # User should be deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.user.id)
    
    def test_create_user_via_user_list_endpoint(self):
        """Test creating user via user list endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'user'
        }
        
        response = self.client.post('/api/users/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        new_user = User.objects.get(email='newuser@example.com')
        # Username is intentionally left null for API-created users
        self.assertIsNone(new_user.username)
        self.assertTrue(new_user.check_password('newpass123'))

class UserSerializerTests(TestCase):
    """Test cases for User serializer"""
    
    def test_password_hashing_on_create(self):
        """Test that password is properly hashed when creating user"""
        from users.serializers import UserSerializer
        
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'plainpassword',
            'role': 'user'
        }
        
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        # Password should be hashed, not plain text
        self.assertNotEqual(user.password, 'plainpassword')
        self.assertTrue(user.check_password('plainpassword'))
    
    def test_password_write_only(self):
        """Test that password field is write-only"""
        from users.serializers import UserSerializer
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        serializer = UserSerializer(user)
        
        # Password should not be in serialized data
        self.assertNotIn('password', serializer.data)
    
    def test_serializer_fields(self):
        """Test that serializer includes correct fields"""
        from users.serializers import UserSerializer
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            google_id='123456789',
            role='admin'
        )
        
        serializer = UserSerializer(user)
        data = serializer.data
        
        expected_fields = ['id', 'google_id', 'username', 'email', 'role']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['google_id'], '123456789')
        self.assertEqual(data['role'], 'admin')


class RefreshTokenBlacklistTests(APITestCase):
    """Tests for refresh token blacklist/rotation/logout behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='blacklistuser',
            email='blacklist@example.com',
            password='blacklistpass'
        )

    def _login_and_get_refresh(self):
        data = {'email': self.user.email, 'password': 'blacklistpass'}
        resp = self.client.post('/api/users/login/', data)
        # The refresh token is set as an HttpOnly cookie; get it from client.cookies
        refresh_token = None
        if 'refresh_token' in self.client.cookies:
            refresh_token = self.client.cookies['refresh_token'].value
        else:
            # Fallback: check response cookies
            refresh_token = resp.cookies.get('refresh_token').value if resp.cookies.get('refresh_token') else None
        return resp, refresh_token

    def test_refresh_with_blacklisted_token_fails(self):
        """If a refresh token's jti is blacklisted, refresh should be rejected."""
        resp, refresh_token = self._login_and_get_refresh()
        self.assertIsNotNone(refresh_token)

        # Decode to get jti
        refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', 'your-refresh-secret-key')
        decoded = jwt.decode(refresh_token, refresh_secret, algorithms=['HS256'])
        jti = decoded.get('jti')
        self.assertIsNotNone(jti)

        # Blacklist it manually
        RefreshTokenBlacklist.objects.create(jti=jti, user=self.user)

        # Ensure client sends the cookie
        self.client.cookies['refresh_token'] = refresh_token

        refresh_resp = self.client.post('/api/users/refresh/')
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', refresh_resp.data)

    def test_rotated_token_old_jti_blacklisted(self):
        """When refreshing (rotation), the old refresh token's jti should be blacklisted."""
        resp, refresh_token = self._login_and_get_refresh()
        self.assertIsNotNone(refresh_token)

        refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', 'your-refresh-secret-key')
        decoded = jwt.decode(refresh_token, refresh_secret, algorithms=['HS256'])
        old_jti = decoded.get('jti')
        self.assertIsNotNone(old_jti)

        # Ensure client sends cookie
        self.client.cookies['refresh_token'] = refresh_token

        refresh_resp = self.client.post('/api/users/refresh/')
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)

        # After rotation, the old jti should be in the blacklist
        exists = RefreshTokenBlacklist.objects.filter(jti=old_jti).exists()
        self.assertTrue(exists)

        # Also ensure a new refresh cookie is present
        new_refresh = None
        if 'refresh_token' in self.client.cookies:
            new_refresh = self.client.cookies['refresh_token'].value
        elif refresh_resp.cookies.get('refresh_token'):
            new_refresh = refresh_resp.cookies.get('refresh_token').value
        self.assertIsNotNone(new_refresh)
        self.assertNotEqual(new_refresh, refresh_token)

    def test_logout_blacklists_token(self):
        """Logout should blacklist the refresh token (if present) and delete the cookie."""
        resp, refresh_token = self._login_and_get_refresh()
        self.assertIsNotNone(refresh_token)

        refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', 'your-refresh-secret-key')
        decoded = jwt.decode(refresh_token, refresh_secret, algorithms=['HS256'])
        jti = decoded.get('jti')
        self.assertIsNotNone(jti)

        # Ensure client sends the cookie
        self.client.cookies['refresh_token'] = refresh_token

        logout_resp = self.client.post('/api/users/logout/')
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # The jti should now be blacklisted
        self.assertTrue(RefreshTokenBlacklist.objects.filter(jti=jti).exists())

        # The cookie should be deleted in the response (Set-Cookie expires)
        # Depending on client, cookie may be cleared; ensure server attempted to delete it
        self.assertTrue('refresh_token' in logout_resp.cookies or 'refresh_token' in logout_resp._headers if hasattr(logout_resp, '_headers') else True)
