"""
Authentication Tests

Tests for user registration, login, profile management, and password change.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    def test_register_success(self, api_client):
        """Test successful user registration."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'timezone': 'America/New_York',
            'daily_task_goal': 10
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == 'newuser@example.com'
    
    def test_register_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePassword123!',
            'password_confirm': 'DifferentPassword123!',
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_duplicate_email(self, api_client, user):
        """Test registration fails with duplicate email."""
        url = '/api/v1/auth/register/'
        data = {
            'email': user.email,  # Existing user's email
            'username': 'differentuser',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = '/api/v1/auth/register/'
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': '123',  # Too weak
            'password_confirm': '123',
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestJWTAuthentication:
    """Tests for JWT token authentication."""
    
    def test_obtain_token(self, api_client, user):
        """Test obtaining JWT token with valid credentials."""
        url = '/api/v1/auth/token/'
        data = {
            'email': user.email,
            'password': 'TestPassword123!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_obtain_token_invalid_credentials(self, api_client, user):
        """Test token request fails with wrong password."""
        url = '/api/v1/auth/token/'
        data = {
            'email': user.email,
            'password': 'WrongPassword!'
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, api_client, user):
        """Test refreshing access token."""
        # First, obtain tokens
        token_url = '/api/v1/auth/token/'
        token_response = api_client.post(token_url, {
            'email': user.email,
            'password': 'TestPassword123!'
        })
        
        refresh_token = token_response.data['refresh']
        
        # Then refresh
        refresh_url = '/api/v1/auth/token/refresh/'
        response = api_client.post(refresh_url, {'refresh': refresh_token})
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data


@pytest.mark.django_db
class TestUserProfile:
    """Tests for user profile endpoint."""
    
    def test_get_profile(self, auth_client, user):
        """Test retrieving user profile."""
        url = '/api/v1/auth/profile/'
        
        response = auth_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['username'] == user.username
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test profile access fails without authentication."""
        url = '/api/v1/auth/profile/'
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile(self, auth_client, user):
        """Test updating user profile."""
        url = '/api/v1/auth/profile/'
        data = {
            'username': 'updatedusername',
            'daily_task_goal': 15,
            'timezone': 'Europe/London'
        }
        
        response = auth_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.username == 'updatedusername'
        assert user.daily_task_goal == 15


@pytest.mark.django_db
class TestChangePassword:
    """Tests for password change endpoint."""
    
    def test_change_password_success(self, auth_client, user):
        """Test successful password change."""
        url = '/api/v1/auth/change-password/'
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewSecurePassword456!',
            'new_password_confirm': 'NewSecurePassword456!'
        }
        
        response = auth_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        
        # Verify new password works
        user.refresh_from_db()
        assert user.check_password('NewSecurePassword456!')
    
    def test_change_password_wrong_old(self, auth_client):
        """Test password change fails with wrong old password."""
        url = '/api/v1/auth/change-password/'
        data = {
            'old_password': 'WrongOldPassword!',
            'new_password': 'NewPassword456!',
            'new_password_confirm': 'NewPassword456!'
        }
        
        response = auth_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_mismatch(self, auth_client):
        """Test password change fails with mismatched new passwords."""
        url = '/api/v1/auth/change-password/'
        data = {
            'old_password': 'TestPassword123!',
            'new_password': 'NewPassword456!',
            'new_password_confirm': 'DifferentPassword!'
        }
        
        response = auth_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
