"""
Model Context Protocol (MCP) Compatible Views

This module provides MCP-compatible endpoints for AI agent integration.
MCP allows AI agents to discover and use API capabilities programmatically.

Reference: https://spec.modelcontextprotocol.io/
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import Task, Category, Tag, Habit, PomodoroSession


class MCPCapabilitiesView(APIView):
    """
    MCP Capabilities Discovery Endpoint
    
    Returns the API's capabilities in MCP format for AI agent integration.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get MCP capabilities",
        description="""
Returns the API capabilities in Model Context Protocol (MCP) format.

This endpoint allows AI agents to discover what operations are available
and how to interact with the API programmatically.
        """,
        tags=['MCP'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'version': {'type': 'string'},
                    'description': {'type': 'string'},
                    'capabilities': {'type': 'object'},
                    'authentication': {'type': 'object'},
                }
            }
        }
    )
    def get(self, request):
        return Response({
            'name': 'Smart Productivity Analytics Platform',
            'version': '1.0.0',
            'description': 'A comprehensive API for task management, habit tracking, and productivity analytics.',
            'protocol': 'MCP/1.0',
            'capabilities': {
                'tools': True,
                'resources': True,
                'prompts': False,
                'sampling': False,
            },
            'authentication': {
                'type': 'bearer',
                'scheme': 'JWT',
                'endpoints': {
                    'token': '/api/v1/auth/token/',
                    'refresh': '/api/v1/auth/token/refresh/',
                    'register': '/api/v1/auth/register/',
                }
            },
            'endpoints': {
                'tools': '/api/v1/mcp/tools/',
                'execute': '/api/v1/mcp/execute/',
            },
            'rate_limits': {
                'authenticated': '1000/hour',
                'anonymous': '100/hour',
            }
        })


class MCPToolsView(APIView):
    """
    MCP Tools Discovery Endpoint
    
    Returns available tools/operations in MCP format.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List available MCP tools",
        description="""
Returns all available tools/operations that can be executed through the MCP interface.

Each tool includes:
- Name and description
- Input schema (JSON Schema format)
- Required authentication level
        """,
        tags=['MCP'],
    )
    def get(self, request):
        tools = [
            {
                'name': 'create_task',
                'description': 'Create a new task with title, description, priority, and optional due date',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Task title',
                            'maxLength': 255
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Detailed task description'
                        },
                        'priority': {
                            'type': 'string',
                            'enum': ['low', 'medium', 'high', 'urgent'],
                            'default': 'medium'
                        },
                        'due_date': {
                            'type': 'string',
                            'format': 'date-time',
                            'description': 'Due date in ISO 8601 format'
                        },
                        'category_id': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Category UUID'
                        },
                        'energy_level': {
                            'type': 'string',
                            'enum': ['low', 'medium', 'high'],
                            'description': 'Required energy level for this task'
                        }
                    },
                    'required': ['title']
                }
            },
            {
                'name': 'list_tasks',
                'description': 'List tasks with optional filtering by status, priority, category, or date range',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'status': {
                            'type': 'string',
                            'enum': ['pending', 'in_progress', 'completed', 'cancelled']
                        },
                        'priority': {
                            'type': 'string',
                            'enum': ['low', 'medium', 'high', 'urgent']
                        },
                        'category_id': {
                            'type': 'string',
                            'format': 'uuid'
                        },
                        'due_before': {
                            'type': 'string',
                            'format': 'date'
                        },
                        'due_after': {
                            'type': 'string',
                            'format': 'date'
                        },
                        'limit': {
                            'type': 'integer',
                            'default': 20,
                            'maximum': 100
                        }
                    }
                }
            },
            {
                'name': 'complete_task',
                'description': 'Mark a task as completed',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'task_id': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'UUID of the task to complete'
                        }
                    },
                    'required': ['task_id']
                }
            },
            {
                'name': 'get_today_tasks',
                'description': 'Get all tasks due today',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            },
            {
                'name': 'get_overdue_tasks',
                'description': 'Get all overdue tasks',
                'inputSchema': {
                    'type': 'object',
                    'properties': {}
                }
            },
            {
                'name': 'start_pomodoro',
                'description': 'Start a new pomodoro focus session',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'task_id': {
                            'type': 'string',
                            'format': 'uuid',
                            'description': 'Optional task to associate with the session'
                        },
                        'duration': {
                            'type': 'integer',
                            'default': 25,
                            'minimum': 1,
                            'maximum': 180,
                            'description': 'Session duration in minutes'
                        }
                    }
                }
            },
            {
                'name': 'complete_habit',
                'description': 'Log a habit completion',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'habit_id': {
                            'type': 'string',
                            'format': 'uuid'
                        },
                        'notes': {
                            'type': 'string'
                        }
                    },
                    'required': ['habit_id']
                }
            },
            {
                'name': 'get_productivity_summary',
                'description': 'Get a summary of productivity metrics for today or a specified period',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'period': {
                            'type': 'string',
                            'enum': ['today', 'week', 'month'],
                            'default': 'today'
                        }
                    }
                }
            },
            {
                'name': 'suggest_next_task',
                'description': 'Get an AI-powered suggestion for the next task to work on based on priority, energy level, and deadlines',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'energy_level': {
                            'type': 'string',
                            'enum': ['low', 'medium', 'high'],
                            'description': 'Current energy level to match tasks'
                        },
                        'available_minutes': {
                            'type': 'integer',
                            'description': 'Available time in minutes'
                        }
                    }
                }
            },
            {
                'name': 'create_category',
                'description': 'Create a new task category',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'maxLength': 100
                        },
                        'color': {
                            'type': 'string',
                            'pattern': '^#[0-9A-Fa-f]{6}$',
                            'default': '#3B82F6'
                        },
                        'description': {
                            'type': 'string'
                        }
                    },
                    'required': ['name']
                }
            }
        ]
        
        return Response({
            'tools': tools,
            'count': len(tools),
        })


class MCPExecuteView(APIView):
    """
    MCP Tool Execution Endpoint
    
    Execute tools/operations via the MCP interface.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Execute an MCP tool",
        description="""
Execute a tool by name with the provided arguments.

**Request Format:**
```json
{
    "tool": "tool_name",
    "arguments": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

**Response Format:**
```json
{
    "success": true,
    "result": { ... },
    "error": null
}
```
        """,
        tags=['MCP'],
        request={
            'type': 'object',
            'properties': {
                'tool': {'type': 'string', 'description': 'Tool name to execute'},
                'arguments': {'type': 'object', 'description': 'Tool arguments'}
            },
            'required': ['tool']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'result': {'type': 'object'},
                    'error': {'type': 'string', 'nullable': True}
                }
            }
        }
    )
    def post(self, request):
        tool_name = request.data.get('tool')
        arguments = request.data.get('arguments', {})
        
        if not tool_name:
            return Response({
                'success': False,
                'result': None,
                'error': 'Tool name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tool dispatcher
        tool_handlers = {
            'create_task': self._create_task,
            'list_tasks': self._list_tasks,
            'complete_task': self._complete_task,
            'get_today_tasks': self._get_today_tasks,
            'get_overdue_tasks': self._get_overdue_tasks,
            'start_pomodoro': self._start_pomodoro,
            'complete_habit': self._complete_habit,
            'get_productivity_summary': self._get_productivity_summary,
            'suggest_next_task': self._suggest_next_task,
            'create_category': self._create_category,
        }
        
        handler = tool_handlers.get(tool_name)
        if not handler:
            return Response({
                'success': False,
                'result': None,
                'error': f'Unknown tool: {tool_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = handler(request.user, arguments)
            return Response({
                'success': True,
                'result': result,
                'error': None
            })
        except Exception as e:
            return Response({
                'success': False,
                'result': None,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_task(self, user, args):
        """Create a new task."""
        task = Task.objects.create(
            user=user,
            title=args.get('title'),
            description=args.get('description', ''),
            priority=args.get('priority', 'medium'),
            energy_level=args.get('energy_level', 'medium'),
            due_date=args.get('due_date'),
            category_id=args.get('category_id'),
        )
        return {
            'id': str(task.id),
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'created_at': task.created_at.isoformat(),
        }
    
    def _list_tasks(self, user, args):
        """List tasks with filtering."""
        queryset = Task.objects.filter(user=user)
        
        if args.get('status'):
            queryset = queryset.filter(status=args['status'])
        if args.get('priority'):
            queryset = queryset.filter(priority=args['priority'])
        if args.get('category_id'):
            queryset = queryset.filter(category_id=args['category_id'])
        if args.get('due_before'):
            queryset = queryset.filter(due_date__lte=args['due_before'])
        if args.get('due_after'):
            queryset = queryset.filter(due_date__gte=args['due_after'])
        
        limit = min(args.get('limit', 20), 100)
        tasks = queryset.order_by('-created_at')[:limit]
        
        return [
            {
                'id': str(t.id),
                'title': t.title,
                'status': t.status,
                'priority': t.priority,
                'due_date': t.due_date.isoformat() if t.due_date else None,
            }
            for t in tasks
        ]
    
    def _complete_task(self, user, args):
        """Mark a task as completed."""
        task = Task.objects.get(user=user, id=args['task_id'])
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        return {
            'id': str(task.id),
            'title': task.title,
            'status': task.status,
            'completed_at': task.completed_at.isoformat(),
        }
    
    def _get_today_tasks(self, user, args):
        """Get tasks due today."""
        today = timezone.now().date()
        tasks = Task.objects.filter(
            user=user,
            due_date__date=today,
            status__in=['pending', 'in_progress']
        )
        return [
            {
                'id': str(t.id),
                'title': t.title,
                'status': t.status,
                'priority': t.priority,
            }
            for t in tasks
        ]
    
    def _get_overdue_tasks(self, user, args):
        """Get overdue tasks."""
        tasks = Task.objects.filter(
            user=user,
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        )
        return [
            {
                'id': str(t.id),
                'title': t.title,
                'priority': t.priority,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'days_overdue': (timezone.now().date() - t.due_date.date()).days if t.due_date else 0,
            }
            for t in tasks
        ]
    
    def _start_pomodoro(self, user, args):
        """Start a pomodoro session."""
        session = PomodoroSession.objects.create(
            user=user,
            task_id=args.get('task_id'),
            session_type='focus',
            planned_duration=args.get('duration', 25),
            status='in_progress',
            start_time=timezone.now(),
        )
        return {
            'id': str(session.id),
            'session_type': session.session_type,
            'planned_duration': session.planned_duration,
            'start_time': session.start_time.isoformat(),
        }
    
    def _complete_habit(self, user, args):
        """Log a habit completion."""
        from core.models import HabitLog
        
        habit = Habit.objects.get(user=user, id=args['habit_id'])
        log = HabitLog.objects.create(
            habit=habit,
            notes=args.get('notes', '')
        )
        habit.update_streak()
        
        return {
            'habit_id': str(habit.id),
            'habit_name': habit.name,
            'current_streak': habit.current_streak,
            'logged_at': log.completed_at.isoformat(),
        }
    
    def _get_productivity_summary(self, user, args):
        """Get productivity summary."""
        from django.db.models import Sum, Count
        
        period = args.get('period', 'today')
        
        if period == 'today':
            start_date = timezone.now().date()
        elif period == 'week':
            start_date = timezone.now().date() - timezone.timedelta(days=7)
        else:  # month
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        
        tasks = Task.objects.filter(user=user, created_at__date__gte=start_date)
        completed = tasks.filter(status='completed').count()
        total = tasks.count()
        
        focus_minutes = PomodoroSession.objects.filter(
            user=user,
            start_time__date__gte=start_date,
            status='completed',
            session_type='focus'
        ).aggregate(total=Sum('actual_duration'))['total'] or 0
        
        habits_completed = Habit.objects.filter(user=user).aggregate(
            total=Sum('current_streak')
        )['total'] or 0
        
        return {
            'period': period,
            'tasks_created': total,
            'tasks_completed': completed,
            'completion_rate': round((completed / max(total, 1)) * 100, 1),
            'focus_minutes': focus_minutes,
            'habits_streak_total': habits_completed,
        }
    
    def _suggest_next_task(self, user, args):
        """Suggest the next task to work on."""
        energy_level = args.get('energy_level')
        available_minutes = args.get('available_minutes')
        
        queryset = Task.objects.filter(
            user=user,
            status__in=['pending', 'in_progress']
        )
        
        # Filter by energy level if provided
        if energy_level:
            queryset = queryset.filter(energy_level=energy_level)
        
        # Filter by time if provided
        if available_minutes:
            queryset = queryset.filter(estimated_minutes__lte=available_minutes)
        
        # Prioritize: overdue > urgent > high priority > due soon
        overdue = queryset.filter(due_date__lt=timezone.now()).order_by('due_date').first()
        if overdue:
            reason = "This task is overdue"
            task = overdue
        else:
            urgent = queryset.filter(priority='urgent').order_by('due_date').first()
            if urgent:
                reason = "This is an urgent priority task"
                task = urgent
            else:
                high = queryset.filter(priority='high').order_by('due_date').first()
                if high:
                    reason = "This is a high priority task"
                    task = high
                else:
                    task = queryset.order_by('due_date', '-priority').first()
                    reason = "This task has the nearest deadline" if task else None
        
        if not task:
            return {
                'suggestion': None,
                'reason': 'No pending tasks found matching your criteria'
            }
        
        return {
            'suggestion': {
                'id': str(task.id),
                'title': task.title,
                'priority': task.priority,
                'energy_level': task.energy_level,
                'estimated_minutes': task.estimated_minutes,
                'due_date': task.due_date.isoformat() if task.due_date else None,
            },
            'reason': reason
        }
    
    def _create_category(self, user, args):
        """Create a new category."""
        category = Category.objects.create(
            user=user,
            name=args['name'],
            color=args.get('color', '#3B82F6'),
            description=args.get('description', ''),
        )
        return {
            'id': str(category.id),
            'name': category.name,
            'color': category.color,
        }
