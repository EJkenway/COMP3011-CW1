"""
Test Configuration and Fixtures

Provides pytest fixtures for comprehensive API testing.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    from core.models import User
    return User.objects.create_user(
        email='testuser@example.com',
        username='testuser',
        password='TestPassword123!',
        timezone='UTC',
        daily_task_goal=5
    )


@pytest.fixture
def another_user(db):
    """Create another test user for permission tests."""
    from core.models import User
    return User.objects.create_user(
        email='another@example.com',
        username='anotheruser',
        password='TestPassword123!',
    )


@pytest.fixture
def auth_client(api_client, user):
    """Return an authenticated API client."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def category(db, user):
    """Create a test category."""
    from core.models import Category
    return Category.objects.create(
        user=user,
        name='Work',
        color='#3B82F6',
        description='Work-related tasks'
    )


@pytest.fixture
def tag(db, user):
    """Create a test tag."""
    from core.models import Tag
    return Tag.objects.create(
        user=user,
        name='Important',
        color='#EF4444'
    )


@pytest.fixture
def task(db, user, category):
    """Create a test task."""
    from core.models import Task
    return Task.objects.create(
        user=user,
        title='Test Task',
        description='This is a test task',
        status='pending',
        priority=3,  # MEDIUM
        category=category,
        due_date=timezone.now() + timedelta(days=1)
    )


@pytest.fixture
def completed_task(db, user):
    """Create a completed task."""
    from core.models import Task
    return Task.objects.create(
        user=user,
        title='Completed Task',
        status='completed',
        completed_at=timezone.now()
    )


@pytest.fixture
def overdue_task(db, user):
    """Create an overdue task."""
    from core.models import Task
    return Task.objects.create(
        user=user,
        title='Overdue Task',
        status='pending',
        priority=4,  # HIGH
        due_date=timezone.now() - timedelta(days=2)
    )
