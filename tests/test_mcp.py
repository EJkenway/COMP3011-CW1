"""
MCP (Model Context Protocol) Integration Tests

Tests for AI agent integration capabilities.
"""
import pytest
from rest_framework import status

from core.models import Task, Category, Habit


@pytest.mark.django_db
class TestMCPCapabilities:
    """Tests for MCP capabilities endpoint."""
    
    def test_get_capabilities_unauthenticated(self, api_client):
        """Test capabilities endpoint is accessible without auth."""
        response = api_client.get('/api/v1/mcp/capabilities/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Smart Productivity Analytics Platform'
        assert response.data['protocol'] == 'MCP/1.0'
        assert 'capabilities' in response.data
        assert 'authentication' in response.data
    
    def test_capabilities_structure(self, api_client):
        """Test capabilities response has correct structure."""
        response = api_client.get('/api/v1/mcp/capabilities/')
        
        assert response.data['capabilities']['tools'] is True
        assert 'endpoints' in response.data
        assert '/api/v1/mcp/tools/' in response.data['endpoints']['tools']


@pytest.mark.django_db
class TestMCPTools:
    """Tests for MCP tools discovery endpoint."""
    
    def test_list_tools_authenticated(self, auth_client):
        """Test listing available tools."""
        response = auth_client.get('/api/v1/mcp/tools/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tools' in response.data
        assert len(response.data['tools']) > 0
    
    def test_list_tools_unauthenticated(self, api_client):
        """Test tools endpoint requires authentication."""
        response = api_client.get('/api/v1/mcp/tools/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_tools_have_required_fields(self, auth_client):
        """Test each tool has required MCP fields."""
        response = auth_client.get('/api/v1/mcp/tools/')
        
        for tool in response.data['tools']:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool
    
    def test_specific_tools_available(self, auth_client):
        """Test specific expected tools are available."""
        response = auth_client.get('/api/v1/mcp/tools/')
        
        tool_names = [t['name'] for t in response.data['tools']]
        
        assert 'create_task' in tool_names
        assert 'list_tasks' in tool_names
        assert 'complete_task' in tool_names
        assert 'start_pomodoro' in tool_names
        assert 'suggest_next_task' in tool_names


@pytest.mark.django_db
class TestMCPExecute:
    """Tests for MCP tool execution endpoint."""
    
    def test_execute_create_task(self, auth_client):
        """Test executing create_task tool."""
        data = {
            'tool': 'create_task',
            'arguments': {
                'title': 'MCP Created Task',
                'priority': 'high',
                'description': 'Created via MCP'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['result']['title'] == 'MCP Created Task'
        assert Task.objects.filter(title='MCP Created Task').exists()
    
    def test_execute_list_tasks(self, auth_client, task):
        """Test executing list_tasks tool."""
        data = {
            'tool': 'list_tasks',
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['result']) >= 1
    
    def test_execute_list_tasks_with_filter(self, auth_client, task, completed_task):
        """Test executing list_tasks with status filter."""
        data = {
            'tool': 'list_tasks',
            'arguments': {
                'status': 'completed'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        # All returned tasks should be completed
        for task_data in response.data['result']:
            assert task_data['status'] == 'completed'
    
    def test_execute_complete_task(self, auth_client, task):
        """Test executing complete_task tool."""
        data = {
            'tool': 'complete_task',
            'arguments': {
                'task_id': str(task.id)
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['result']['status'] == 'completed'
        
        task.refresh_from_db()
        assert task.status == 'completed'
    
    def test_execute_get_today_tasks(self, auth_client, user):
        """Test executing get_today_tasks tool."""
        from django.utils import timezone
        Task.objects.create(
            user=user,
            title='Today Task',
            due_date=timezone.now()
        )
        
        data = {
            'tool': 'get_today_tasks',
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
    
    def test_execute_get_overdue_tasks(self, auth_client, overdue_task):
        """Test executing get_overdue_tasks tool."""
        data = {
            'tool': 'get_overdue_tasks',
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['result']) >= 1
        assert 'days_overdue' in response.data['result'][0]
    
    def test_execute_start_pomodoro(self, auth_client, task):
        """Test executing start_pomodoro tool."""
        data = {
            'tool': 'start_pomodoro',
            'arguments': {
                'task_id': str(task.id),
                'duration': 25
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['result']['planned_duration'] == 25
    
    def test_execute_complete_habit(self, auth_client, habit):
        """Test executing complete_habit tool."""
        data = {
            'tool': 'complete_habit',
            'arguments': {
                'habit_id': str(habit.id),
                'notes': 'Completed via MCP'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['result']['habit_name'] == habit.name
    
    def test_execute_get_productivity_summary(self, auth_client):
        """Test executing get_productivity_summary tool."""
        data = {
            'tool': 'get_productivity_summary',
            'arguments': {
                'period': 'today'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'tasks_created' in response.data['result']
        assert 'tasks_completed' in response.data['result']
        assert 'completion_rate' in response.data['result']
    
    def test_execute_suggest_next_task(self, auth_client, task, overdue_task):
        """Test executing suggest_next_task tool."""
        data = {
            'tool': 'suggest_next_task',
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'suggestion' in response.data['result']
        assert 'reason' in response.data['result']
        # Should suggest overdue task first
        if response.data['result']['suggestion']:
            assert response.data['result']['suggestion']['id'] == str(overdue_task.id)
    
    def test_execute_suggest_next_task_with_energy(self, auth_client, user):
        """Test suggest_next_task with energy level filter."""
        Task.objects.create(
            user=user,
            title='Low Energy Task',
            energy_level='low',
            status='pending'
        )
        Task.objects.create(
            user=user,
            title='High Energy Task',
            energy_level='high',
            status='pending'
        )
        
        data = {
            'tool': 'suggest_next_task',
            'arguments': {
                'energy_level': 'low'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        if response.data['result']['suggestion']:
            assert response.data['result']['suggestion']['energy_level'] == 'low'
    
    def test_execute_create_category(self, auth_client):
        """Test executing create_category tool."""
        data = {
            'tool': 'create_category',
            'arguments': {
                'name': 'MCP Category',
                'color': '#FF5733'
            }
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['result']['name'] == 'MCP Category'
        assert Category.objects.filter(name='MCP Category').exists()
    
    def test_execute_unknown_tool(self, auth_client):
        """Test executing unknown tool returns error."""
        data = {
            'tool': 'nonexistent_tool',
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'Unknown tool' in response.data['error']
    
    def test_execute_missing_tool_name(self, auth_client):
        """Test execute without tool name returns error."""
        data = {
            'arguments': {}
        }
        
        response = auth_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
    
    def test_execute_unauthenticated(self, api_client):
        """Test execute endpoint requires authentication."""
        data = {
            'tool': 'list_tasks',
            'arguments': {}
        }
        
        response = api_client.post('/api/v1/mcp/execute/', data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
