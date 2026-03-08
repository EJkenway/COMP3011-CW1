"""
Task API Tests

Comprehensive tests for task CRUD operations, filtering, and custom actions.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status

from core.models import Task


@pytest.mark.django_db
class TestTaskList:
    """Tests for task list endpoint."""
    
    def test_list_tasks_empty(self, auth_client):
        """Test listing tasks when none exist."""
        response = auth_client.get('/api/v1/tasks/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
    
    def test_list_tasks(self, auth_client, task):
        """Test listing tasks."""
        response = auth_client.get('/api/v1/tasks/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['title'] == task.title
    
    def test_list_tasks_filter_by_status(self, auth_client, task, completed_task):
        """Test filtering tasks by status."""
        response = auth_client.get('/api/v1/tasks/', {'status': 'pending'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'pending'
    
    def test_list_tasks_filter_by_priority(self, auth_client, user):
        """Test filtering tasks by priority."""
        Task.objects.create(user=user, title='High Priority', priority='high')
        Task.objects.create(user=user, title='Low Priority', priority='low')
        
        response = auth_client.get('/api/v1/tasks/', {'priority': 'high'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['priority'] == 'high'
    
    def test_list_tasks_search(self, auth_client, user):
        """Test searching tasks."""
        Task.objects.create(user=user, title='Buy groceries')
        Task.objects.create(user=user, title='Call mom')
        
        response = auth_client.get('/api/v1/tasks/', {'search': 'groceries'})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert 'groceries' in response.data['results'][0]['title'].lower()
    
    def test_list_tasks_ordering(self, auth_client, user):
        """Test ordering tasks."""
        task1 = Task.objects.create(user=user, title='First', priority='low')
        task2 = Task.objects.create(user=user, title='Second', priority='urgent')
        
        response = auth_client.get('/api/v1/tasks/', {'ordering': '-priority'})
        
        assert response.status_code == status.HTTP_200_OK
        # Urgent should come first
        assert response.data['results'][0]['priority'] == 'urgent'
    
    def test_list_tasks_pagination(self, auth_client, user):
        """Test task pagination."""
        # Create 25 tasks
        for i in range(25):
            Task.objects.create(user=user, title=f'Task {i}')
        
        response = auth_client.get('/api/v1/tasks/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20  # Default page size
        assert 'next' in response.data


@pytest.mark.django_db
class TestTaskCreate:
    """Tests for task creation."""
    
    def test_create_task_minimal(self, auth_client):
        """Test creating a task with minimal data."""
        data = {'title': 'New Task'}
        
        response = auth_client.post('/api/v1/tasks/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Task.objects.filter(title='New Task').exists()
    
    def test_create_task_full(self, auth_client, category, tag):
        """Test creating a task with all fields."""
        data = {
            'title': 'Complete Project',
            'description': 'Finish the API project',
            'status': 'pending',
            'priority': 'high',
            'energy_level': 'high',
            'category': str(category.id),
            'tags': [str(tag.id)],
            'due_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'estimated_minutes': 120,
        }
        
        response = auth_client.post('/api/v1/tasks/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        task = Task.objects.get(title='Complete Project')
        assert task.priority == 'high'
        assert task.category == category
        assert tag in task.tags.all()
    
    def test_create_task_invalid_priority(self, auth_client):
        """Test creating task with invalid priority fails."""
        data = {
            'title': 'Bad Task',
            'priority': 'invalid_priority'
        }
        
        response = auth_client.post('/api/v1/tasks/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskRetrieve:
    """Tests for task retrieval."""
    
    def test_retrieve_task(self, auth_client, task):
        """Test retrieving a single task."""
        response = auth_client.get(f'/api/v1/tasks/{task.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == task.title
        assert response.data['description'] == task.description
    
    def test_retrieve_task_not_found(self, auth_client):
        """Test retrieving non-existent task."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = auth_client.get(f'/api/v1/tasks/{fake_id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_other_user_task(self, auth_client, another_user):
        """Test retrieving another user's task fails."""
        other_task = Task.objects.create(
            user=another_user,
            title='Other User Task'
        )
        
        response = auth_client.get(f'/api/v1/tasks/{other_task.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaskUpdate:
    """Tests for task updates."""
    
    def test_update_task_partial(self, auth_client, task):
        """Test partial task update."""
        data = {'title': 'Updated Title'}
        
        response = auth_client.patch(f'/api/v1/tasks/{task.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Updated Title'
    
    def test_update_task_full(self, auth_client, task):
        """Test full task update."""
        data = {
            'title': 'Completely Updated',
            'description': 'New description',
            'priority': 'urgent',
            'status': 'in_progress'
        }
        
        response = auth_client.put(f'/api/v1/tasks/{task.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Completely Updated'
        assert task.priority == 'urgent'
    
    def test_update_other_user_task(self, auth_client, another_user):
        """Test updating another user's task fails."""
        other_task = Task.objects.create(
            user=another_user,
            title='Other User Task'
        )
        
        response = auth_client.patch(
            f'/api/v1/tasks/{other_task.id}/',
            {'title': 'Hacked!'}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaskDelete:
    """Tests for task deletion."""
    
    def test_delete_task(self, auth_client, task):
        """Test deleting a task."""
        task_id = task.id
        
        response = auth_client.delete(f'/api/v1/tasks/{task.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(id=task_id).exists()
    
    def test_delete_other_user_task(self, auth_client, another_user):
        """Test deleting another user's task fails."""
        other_task = Task.objects.create(
            user=another_user,
            title='Other User Task'
        )
        
        response = auth_client.delete(f'/api/v1/tasks/{other_task.id}/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Task.objects.filter(id=other_task.id).exists()


@pytest.mark.django_db
class TestTaskActions:
    """Tests for task custom actions."""
    
    def test_complete_task(self, auth_client, task):
        """Test marking a task as completed."""
        response = auth_client.post(f'/api/v1/tasks/{task.id}/complete/')
        
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == 'completed'
        assert task.completed_at is not None
    
    def test_reopen_task(self, auth_client, completed_task):
        """Test reopening a completed task."""
        response = auth_client.post(f'/api/v1/tasks/{completed_task.id}/reopen/')
        
        assert response.status_code == status.HTTP_200_OK
        completed_task.refresh_from_db()
        assert completed_task.status == 'pending'
        assert completed_task.completed_at is None
    
    def test_get_today_tasks(self, auth_client, user):
        """Test getting today's tasks."""
        # Create a task due today
        Task.objects.create(
            user=user,
            title='Today Task',
            due_date=timezone.now()
        )
        # Create a task due tomorrow
        Task.objects.create(
            user=user,
            title='Tomorrow Task',
            due_date=timezone.now() + timedelta(days=1)
        )
        
        response = auth_client.get('/api/v1/tasks/today/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Today Task'
    
    def test_get_overdue_tasks(self, auth_client, overdue_task, task):
        """Test getting overdue tasks."""
        response = auth_client.get('/api/v1/tasks/overdue/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == 'Overdue Task'
    
    def test_bulk_update_status(self, auth_client, user):
        """Test bulk status update."""
        task1 = Task.objects.create(user=user, title='Task 1', status='pending')
        task2 = Task.objects.create(user=user, title='Task 2', status='pending')
        
        data = {
            'task_ids': [str(task1.id), str(task2.id)],
            'status': 'completed'
        }
        
        response = auth_client.post('/api/v1/tasks/bulk_update_status/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_count'] == 2
        
        task1.refresh_from_db()
        task2.refresh_from_db()
        assert task1.status == 'completed'
        assert task2.status == 'completed'
