"""
Task, Category, and Tag Views
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from core.models import Category, Tag, Task
from api.serializers.tasks import (
    CategorySerializer,
    TagSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Get all categories for the authenticated user.",
        tags=['Categories'],
    ),
    create=extend_schema(
        summary="Create a category",
        description="Create a new task category.",
        tags=['Categories'],
    ),
    retrieve=extend_schema(
        summary="Get category details",
        description="Retrieve details of a specific category.",
        tags=['Categories'],
    ),
    update=extend_schema(
        summary="Update a category",
        description="Update all fields of a category.",
        tags=['Categories'],
    ),
    partial_update=extend_schema(
        summary="Partially update a category",
        description="Update specific fields of a category.",
        tags=['Categories'],
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Delete a category. Tasks in this category will have their category set to null.",
        tags=['Categories'],
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task categories.
    
    Provides CRUD operations for hierarchical categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.none()  # Required for drf-spectacular
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter categories to current user only."""
        if getattr(self, 'swagger_fake_view', False):
            return Category.objects.none()
        return Category.objects.filter(
            user=self.request.user
        ).select_related('parent').prefetch_related('subcategories')
    
    @extend_schema(
        summary="Get category statistics",
        description="Get task statistics for a specific category.",
        tags=['Categories'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_tasks': {'type': 'integer'},
                    'completed_tasks': {'type': 'integer'},
                    'pending_tasks': {'type': 'integer'},
                    'overdue_tasks': {'type': 'integer'},
                }
            }
        }
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics for a category."""
        category = self.get_object()
        tasks = category.tasks.all()
        
        return Response({
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='completed').count(),
            'pending_tasks': tasks.filter(status__in=['pending', 'in_progress']).count(),
            'overdue_tasks': tasks.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=timezone.now()
            ).count(),
        })


@extend_schema_view(
    list=extend_schema(
        summary="List all tags",
        description="Get all tags for the authenticated user.",
        tags=['Tags'],
    ),
    create=extend_schema(
        summary="Create a tag",
        description="Create a new task tag.",
        tags=['Tags'],
    ),
    retrieve=extend_schema(
        summary="Get tag details",
        description="Retrieve details of a specific tag.",
        tags=['Tags'],
    ),
    update=extend_schema(
        summary="Update a tag",
        description="Update all fields of a tag.",
        tags=['Tags'],
    ),
    partial_update=extend_schema(
        summary="Partially update a tag",
        description="Update specific fields of a tag.",
        tags=['Tags'],
    ),
    destroy=extend_schema(
        summary="Delete a tag",
        description="Delete a tag. The tag will be removed from all associated tasks.",
        tags=['Tags'],
    ),
)
class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task tags.
    
    Provides CRUD operations for flexible tagging.
    """
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    queryset = Tag.objects.none()  # Required for drf-spectacular
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter tags to current user only."""
        if getattr(self, 'swagger_fake_view', False):
            return Tag.objects.none()
        return Tag.objects.filter(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="List all tasks",
        description="""
Get all tasks for the authenticated user with filtering and sorting.

**Filters:**
- `status`: Filter by status (pending, in_progress, completed, cancelled)
- `priority`: Filter by priority (low, medium, high, urgent)
- `category`: Filter by category ID
- `energy_level`: Filter by energy level (low, medium, high)
- `due_date_before`: Tasks due before this date
- `due_date_after`: Tasks due after this date
- `is_overdue`: Filter overdue tasks (true/false)

**Search:**
- Search in title and description

**Ordering:**
- created_at, due_date, priority, status
        """,
        tags=['Tasks'],
        parameters=[
            OpenApiParameter(name='status', description='Filter by status'),
            OpenApiParameter(name='priority', description='Filter by priority'),
            OpenApiParameter(name='category', description='Filter by category ID'),
            OpenApiParameter(name='is_overdue', description='Filter overdue tasks', type=bool),
        ]
    ),
    create=extend_schema(
        summary="Create a task",
        description="Create a new task with optional category and tags.",
        tags=['Tasks'],
    ),
    retrieve=extend_schema(
        summary="Get task details",
        description="Retrieve full details of a specific task.",
        tags=['Tasks'],
    ),
    update=extend_schema(
        summary="Update a task",
        description="Update all fields of a task.",
        tags=['Tasks'],
    ),
    partial_update=extend_schema(
        summary="Partially update a task",
        description="Update specific fields of a task.",
        tags=['Tasks'],
    ),
    destroy=extend_schema(
        summary="Delete a task",
        description="Delete a task and all associated data.",
        tags=['Tasks'],
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    
    Provides full CRUD operations with filtering, searching, and custom actions.
    """
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.none()  # Required for drf-spectacular
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'energy_level']
    search_fields = ['title', 'description', 'notes']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter tasks to current user with optimized queries."""
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()
        
        queryset = Task.objects.filter(
            user=self.request.user
        ).select_related('category').prefetch_related('tags')
        
        # Custom filters
        params = self.request.query_params
        
        # Filter by overdue status
        is_overdue = params.get('is_overdue')
        if is_overdue is not None:
            if is_overdue.lower() == 'true':
                queryset = queryset.filter(
                    status__in=['pending', 'in_progress'],
                    due_date__lt=timezone.now()
                )
            elif is_overdue.lower() == 'false':
                queryset = queryset.exclude(
                    status__in=['pending', 'in_progress'],
                    due_date__lt=timezone.now()
                )
        
        # Filter by date range
        due_before = params.get('due_date_before')
        if due_before:
            queryset = queryset.filter(due_date__lte=due_before)
        
        due_after = params.get('due_date_after')
        if due_after:
            queryset = queryset.filter(due_date__gte=due_after)
        
        # Filter by tags
        tags = params.get('tags')
        if tags:
            tag_ids = [int(t) for t in tags.split(',') if t.isdigit()]
            if tag_ids:
                queryset = queryset.filter(tags__id__in=tag_ids).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer
    
    @extend_schema(
        summary="Mark task as completed",
        description="Mark a task as completed and record completion time.",
        tags=['Tasks'],
        request=None,
        responses={
            200: TaskDetailSerializer
        }
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed."""
        task = self.get_object()
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        return Response(TaskDetailSerializer(task).data)
    
    @extend_schema(
        summary="Reopen a completed task",
        description="Reopen a previously completed task.",
        tags=['Tasks'],
        request=None,
        responses={
            200: TaskDetailSerializer
        }
    )
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen a completed task."""
        task = self.get_object()
        task.status = 'pending'
        task.completed_at = None
        task.save()
        
        return Response(TaskDetailSerializer(task).data)
    
    @extend_schema(
        summary="Get subtasks",
        description="Get all subtasks of a task.",
        tags=['Tasks'],
        responses={
            200: TaskListSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'])
    def subtasks(self, request, pk=None):
        """Get subtasks for a task."""
        task = self.get_object()
        subtasks = Task.objects.filter(
            user=request.user,
            parent_task=task
        )
        serializer = TaskListSerializer(subtasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get today's tasks",
        description="Get all tasks due today.",
        tags=['Tasks'],
        responses={
            200: TaskListSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get tasks due today."""
        today = timezone.now().date()
        tasks = self.get_queryset().filter(
            due_date__date=today,
            status__in=['pending', 'in_progress']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get overdue tasks",
        description="Get all overdue tasks.",
        tags=['Tasks'],
        responses={
            200: TaskListSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks."""
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Bulk update task status",
        description="Update status for multiple tasks at once.",
        tags=['Tasks'],
        request={
            'type': 'object',
            'properties': {
                'task_ids': {'type': 'array', 'items': {'type': 'string'}},
                'status': {'type': 'string', 'enum': ['pending', 'in_progress', 'completed', 'cancelled']}
            },
            'required': ['task_ids', 'status']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'updated_count': {'type': 'integer'},
                    'message': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """Bulk update task status."""
        task_ids = request.data.get('task_ids', [])
        new_status = request.data.get('status')
        
        if not task_ids or not new_status:
            return Response(
                {'error': 'task_ids and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = Task.objects.filter(
            user=request.user,
            id__in=task_ids
        ).update(
            status=new_status,
            completed_at=timezone.now() if new_status == 'completed' else None
        )
        
        return Response({
            'updated_count': updated,
            'message': f'{updated} tasks updated to {new_status}'
        })
