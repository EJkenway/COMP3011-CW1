"""
Productivity Feature Views (Pomodoro Sessions and Habits)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from core.models import PomodoroSession, Habit, HabitLog
from api.serializers.productivity import (
    PomodoroSessionSerializer,
    PomodoroSessionCreateSerializer,
    HabitSerializer,
    HabitCreateUpdateSerializer,
    HabitLogSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List pomodoro sessions",
        description="Get all pomodoro sessions for the authenticated user.",
        tags=['Pomodoro'],
    ),
    create=extend_schema(
        summary="Start a pomodoro session",
        description="Start a new pomodoro or break session.",
        tags=['Pomodoro'],
    ),
    retrieve=extend_schema(
        summary="Get session details",
        description="Retrieve details of a specific pomodoro session.",
        tags=['Pomodoro'],
    ),
    destroy=extend_schema(
        summary="Delete a session",
        description="Delete a pomodoro session.",
        tags=['Pomodoro'],
    ),
)
class PomodoroSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pomodoro sessions.
    
    Provides operations for starting, completing, and tracking focus sessions.
    """
    permission_classes = [IsAuthenticated]
    queryset = PomodoroSession.objects.none()  # Required for drf-spectacular
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session_type', 'status', 'task']
    ordering_fields = ['start_time', 'created_at']
    ordering = ['-start_time']
    
    def get_queryset(self):
        """Filter sessions to current user."""
        if getattr(self, 'swagger_fake_view', False):
            return PomodoroSession.objects.none()
        return PomodoroSession.objects.filter(
            user=self.request.user
        ).select_related('task')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PomodoroSessionCreateSerializer
        return PomodoroSessionSerializer
    
    @extend_schema(
        summary="Complete a pomodoro session",
        description="Mark an in-progress session as completed.",
        tags=['Pomodoro'],
        request={
            'type': 'object',
            'properties': {
                'interruptions_count': {'type': 'integer', 'default': 0},
                'notes': {'type': 'string'}
            }
        },
        responses={
            200: PomodoroSessionSerializer
        }
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a pomodoro session."""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Only active sessions can be completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'completed'
        session.end_time = timezone.now()
        session.actual_duration = int(
            (session.end_time - session.start_time).total_seconds() / 60
        )
        session.interruptions_count = request.data.get('interruptions_count', 0)
        
        if 'notes' in request.data:
            session.notes = request.data['notes']
        
        session.save()
        
        return Response(PomodoroSessionSerializer(session).data)
    
    @extend_schema(
        summary="Cancel a pomodoro session",
        description="Cancel an in-progress session.",
        tags=['Pomodoro'],
        request=None,
        responses={
            200: PomodoroSessionSerializer
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an in-progress session."""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Only active sessions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'cancelled'
        session.end_time = timezone.now()
        session.actual_duration = int(
            (session.end_time - session.start_time).total_seconds() / 60
        )
        session.save()
        
        return Response(PomodoroSessionSerializer(session).data)
    
    @extend_schema(
        summary="Get active session",
        description="Get the currently active pomodoro session, if any.",
        tags=['Pomodoro'],
        responses={
            200: PomodoroSessionSerializer
        }
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active session."""
        session = self.get_queryset().filter(status='active').first()
        
        if not session:
            return Response(
                {'message': 'No active session'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(PomodoroSessionSerializer(session).data)
    
    @extend_schema(
        summary="Get today's focus summary",
        description="Get focus time summary for today.",
        tags=['Pomodoro'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_sessions': {'type': 'integer'},
                    'completed_sessions': {'type': 'integer'},
                    'total_focus_minutes': {'type': 'integer'},
                    'total_break_minutes': {'type': 'integer'},
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def today_summary(self, request):
        """Get today's pomodoro summary."""
        today = timezone.now().date()
        sessions = self.get_queryset().filter(start_time__date=today)
        
        focus_sessions = sessions.filter(session_type='focus', status='completed')
        break_sessions = sessions.filter(session_type__in=['short_break', 'long_break'], status='completed')
        
        return Response({
            'total_sessions': sessions.count(),
            'completed_sessions': sessions.filter(status='completed').count(),
            'total_focus_minutes': focus_sessions.aggregate(
                total=Sum('actual_duration')
            )['total'] or 0,
            'total_break_minutes': break_sessions.aggregate(
                total=Sum('actual_duration')
            )['total'] or 0,
        })


@extend_schema_view(
    list=extend_schema(
        summary="List all habits",
        description="Get all habits for the authenticated user.",
        tags=['Habits'],
    ),
    create=extend_schema(
        summary="Create a habit",
        description="Create a new habit to track.",
        tags=['Habits'],
    ),
    retrieve=extend_schema(
        summary="Get habit details",
        description="Retrieve details of a specific habit.",
        tags=['Habits'],
    ),
    update=extend_schema(
        summary="Update a habit",
        description="Update all fields of a habit.",
        tags=['Habits'],
    ),
    partial_update=extend_schema(
        summary="Partially update a habit",
        description="Update specific fields of a habit.",
        tags=['Habits'],
    ),
    destroy=extend_schema(
        summary="Delete a habit",
        description="Delete a habit and all associated logs.",
        tags=['Habits'],
    ),
)
class HabitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing habits.
    
    Provides operations for habit tracking with streak management.
    """
    permission_classes = [IsAuthenticated]
    queryset = Habit.objects.none()  # Required for drf-spectacular
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['frequency', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'current_streak', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter habits to current user."""
        if getattr(self, 'swagger_fake_view', False):
            return Habit.objects.none()
        return Habit.objects.filter(
            user=self.request.user
        ).prefetch_related('logs')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return HabitCreateUpdateSerializer
        return HabitSerializer
    
    @extend_schema(
        summary="Log habit completion",
        description="Record a completion of this habit. Updates streak automatically.",
        tags=['Habits'],
        request={
            'type': 'object',
            'properties': {
                'notes': {'type': 'string', 'description': 'Optional notes about this completion'}
            }
        },
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'log': {'type': 'object'},
                    'habit': {'type': 'object'},
                    'message': {'type': 'string'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Log a habit completion."""
        habit = self.get_object()
        
        # Create log entry
        log = HabitLog.objects.create(
            habit=habit,
            notes=request.data.get('notes', '')
        )
        
        # Update streak
        habit.update_streak()
        habit.refresh_from_db()
        
        return Response({
            'log': HabitLogSerializer(log).data,
            'habit': HabitSerializer(habit).data,
            'message': f'Habit completed! Current streak: {habit.current_streak}'
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Get habit completion history",
        description="Get completion log history for a habit.",
        tags=['Habits'],
        parameters=[
            OpenApiParameter(name='days', description='Number of days to look back', type=int, default=30)
        ],
        responses={
            200: HabitLogSerializer(many=True)
        }
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get habit completion history."""
        habit = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        from datetime import timedelta
        start_date = timezone.now() - timedelta(days=days)
        
        logs = habit.logs.filter(completed_at__gte=start_date).order_by('-completed_at')
        
        return Response(HabitLogSerializer(logs, many=True).data)
    
    @extend_schema(
        summary="Get today's habits",
        description="Get all active habits that should be completed today.",
        tags=['Habits'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'habits': {'type': 'array'},
                    'completed_today': {'type': 'integer'},
                    'remaining': {'type': 'integer'}
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's habits status."""
        today = timezone.now().date()
        habits = self.get_queryset().filter(is_active=True)
        
        result = []
        completed_count = 0
        
        for habit in habits:
            # Check if habit should be done today based on frequency
            should_do_today = True  # Simplified - could be extended for weekly/monthly
            
            # Check if already completed today
            completed_today = habit.logs.filter(completed_at__date=today).count()
            is_done = completed_today >= habit.target_count
            
            if is_done:
                completed_count += 1
            
            result.append({
                'id': str(habit.id),
                'name': habit.name,
                'frequency': habit.frequency,
                'target_count': habit.target_count,
                'completed_today': completed_today,
                'is_done': is_done,
                'current_streak': habit.current_streak,
            })
        
        return Response({
            'habits': result,
            'completed_today': completed_count,
            'remaining': len(result) - completed_count
        })
    
    @extend_schema(
        summary="Reset habit streak",
        description="Reset the streak for a habit (admin action).",
        tags=['Habits'],
        request=None,
        responses={
            200: HabitSerializer
        }
    )
    @action(detail=True, methods=['post'])
    def reset_streak(self, request, pk=None):
        """Reset habit streak."""
        habit = self.get_object()
        habit.current_streak = 0
        habit.save()
        
        return Response(HabitSerializer(habit).data)
