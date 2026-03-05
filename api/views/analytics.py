"""
Analytics and Statistics Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncDate, TruncHour, ExtractHour
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.models import Task, PomodoroSession, Habit, HabitLog, ProductivitySnapshot


class AnalyticsDashboardView(APIView):
    """
    Dashboard analytics endpoint.
    
    Provides comprehensive overview statistics.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get dashboard analytics",
        description="""
Get comprehensive dashboard statistics including:
- Today's progress
- Weekly summary
- Habit status
- Recent activity
        """,
        tags=['Analytics'],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'today': {'type': 'object'},
                    'week': {'type': 'object'},
                    'habits': {'type': 'object'},
                    'recent_tasks': {'type': 'array'},
                }
            }
        }
    )
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Today's stats
        today_tasks = Task.objects.filter(user=user, created_at__date=today)
        today_completed = Task.objects.filter(
            user=user, status='completed', completed_at__date=today
        )
        today_pomodoros = PomodoroSession.objects.filter(
            user=user, start_time__date=today, status='completed'
        )
        
        # Weekly stats
        week_tasks = Task.objects.filter(
            user=user, created_at__date__gte=week_start
        )
        week_completed = Task.objects.filter(
            user=user, status='completed', completed_at__date__gte=week_start
        )
        week_focus = today_pomodoros.aggregate(
            total=Sum('actual_duration')
        )['total'] or 0
        
        # Habits
        active_habits = Habit.objects.filter(user=user, is_active=True)
        habits_done_today = 0
        for habit in active_habits:
            if habit.logs.filter(completed_at__date=today).count() >= habit.target_count:
                habits_done_today += 1
        
        # Recent tasks
        recent_tasks = Task.objects.filter(user=user).order_by('-updated_at')[:5]
        
        return Response({
            'today': {
                'tasks_created': today_tasks.count(),
                'tasks_completed': today_completed.count(),
                'focus_minutes': today_pomodoros.aggregate(
                    total=Sum('actual_duration')
                )['total'] or 0,
                'pomodoro_sessions': today_pomodoros.count(),
            },
            'week': {
                'tasks_created': week_tasks.count(),
                'tasks_completed': week_completed.count(),
                'completion_rate': round(
                    (week_completed.count() / max(week_tasks.count(), 1)) * 100, 1
                ),
                'total_focus_minutes': week_focus,
            },
            'habits': {
                'total_active': active_habits.count(),
                'completed_today': habits_done_today,
                'best_streak': active_habits.aggregate(
                    best=Avg('best_streak')
                )['best'] or 0,
            },
            'recent_tasks': [
                {
                    'id': str(t.id),
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'updated_at': t.updated_at.isoformat(),
                }
                for t in recent_tasks
            ]
        })


class TaskAnalyticsView(APIView):
    """
    Task-specific analytics endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get task analytics",
        description="Get detailed task statistics and distributions.",
        tags=['Analytics'],
        parameters=[
            OpenApiParameter(
                name='days',
                description='Number of days to analyze',
                type=int,
                default=30
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_tasks': {'type': 'integer'},
                    'completed_tasks': {'type': 'integer'},
                    'pending_tasks': {'type': 'integer'},
                    'in_progress_tasks': {'type': 'integer'},
                    'overdue_tasks': {'type': 'integer'},
                    'completion_rate': {'type': 'number'},
                    'avg_completion_time_minutes': {'type': 'number', 'nullable': True},
                    'by_priority': {'type': 'object'},
                    'by_energy_level': {'type': 'object'},
                    'by_category': {'type': 'array'},
                    'completion_by_hour': {'type': 'array'},
                    'completion_by_day': {'type': 'array'},
                }
            }
        }
    )
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        tasks = Task.objects.filter(user=user, created_at__gte=start_date)
        
        # Basic counts
        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        pending = tasks.filter(status='pending').count()
        in_progress = tasks.filter(status='in_progress').count()
        overdue = tasks.filter(
            status__in=['pending', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        
        # By priority
        by_priority = dict(
            tasks.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )
        
        # By energy level
        by_energy = dict(
            tasks.values('energy_level').annotate(count=Count('id')).values_list('energy_level', 'count')
        )
        
        # By category
        by_category = list(
            tasks.exclude(category__isnull=True)
            .values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Completion by hour
        completion_by_hour = list(
            tasks.filter(status='completed', completed_at__isnull=False)
            .annotate(hour=ExtractHour('completed_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        # Completion by day
        completion_by_day = list(
            tasks.filter(status='completed')
            .annotate(date=TruncDate('completed_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        # Average completion time
        completed_tasks = tasks.filter(
            status='completed',
            actual_minutes__isnull=False
        )
        avg_time = completed_tasks.aggregate(avg=Avg('actual_minutes'))['avg']
        
        return Response({
            'total_tasks': total,
            'completed_tasks': completed,
            'pending_tasks': pending,
            'in_progress_tasks': in_progress,
            'overdue_tasks': overdue,
            'completion_rate': round((completed / max(total, 1)) * 100, 1),
            'avg_completion_time_minutes': avg_time,
            'by_priority': by_priority,
            'by_energy_level': by_energy,
            'by_category': by_category,
            'completion_by_hour': completion_by_hour,
            'completion_by_day': [
                {'date': item['date'].isoformat() if item['date'] else None, 'count': item['count']}
                for item in completion_by_day
            ],
        })


class HabitAnalyticsView(APIView):
    """
    Habit-specific analytics endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get habit analytics",
        description="Get detailed habit statistics and performance data.",
        tags=['Analytics'],
        parameters=[
            OpenApiParameter(
                name='days',
                description='Number of days to analyze',
                type=int,
                default=30
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_habits': {'type': 'integer'},
                    'active_habits': {'type': 'integer'},
                    'total_completions': {'type': 'integer'},
                    'avg_completion_rate': {'type': 'number'},
                    'longest_streak': {'type': 'integer'},
                    'current_longest_streak': {'type': 'integer'},
                    'habits_summary': {'type': 'array'},
                    'best_performing_habits': {'type': 'array'},
                    'needs_attention': {'type': 'array'},
                    'completion_heatmap': {'type': 'array'},
                }
            }
        }
    )
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        habits = Habit.objects.filter(user=user)
        active_habits = habits.filter(is_active=True)
        
        # Total completions
        total_completions = HabitLog.objects.filter(
            habit__user=user,
            completed_at__gte=start_date
        ).count()
        
        # Streaks
        longest_streak = habits.order_by('-best_streak').first()
        current_longest = active_habits.order_by('-current_streak').first()
        
        # Habits summary
        habits_summary = []
        for habit in active_habits:
            completions = habit.logs.filter(completed_at__gte=start_date).count()
            expected = days * habit.target_count if habit.frequency == 'daily' else (days // 7) * habit.target_count
            rate = (completions / max(expected, 1)) * 100
            
            habits_summary.append({
                'id': str(habit.id),
                'name': habit.name,
                'frequency': habit.frequency,
                'completions': completions,
                'current_streak': habit.current_streak,
                'best_streak': habit.best_streak,
                'completion_rate': round(rate, 1),
            })
        
        # Sort by performance
        best_performing = sorted(habits_summary, key=lambda x: x['completion_rate'], reverse=True)[:5]
        needs_attention = sorted(
            [h for h in habits_summary if h['completion_rate'] < 50],
            key=lambda x: x['completion_rate']
        )[:5]
        
        # Completion heatmap (last 30 days)
        heatmap = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            count = HabitLog.objects.filter(
                habit__user=user,
                completed_at__date=date
            ).count()
            heatmap.append({
                'date': date.isoformat(),
                'count': count
            })
        
        return Response({
            'total_habits': habits.count(),
            'active_habits': active_habits.count(),
            'total_completions': total_completions,
            'avg_completion_rate': round(
                sum(h['completion_rate'] for h in habits_summary) / max(len(habits_summary), 1), 1
            ),
            'longest_streak': longest_streak.best_streak if longest_streak else 0,
            'current_longest_streak': current_longest.current_streak if current_longest else 0,
            'habits_summary': habits_summary,
            'best_performing_habits': best_performing,
            'needs_attention': needs_attention,
            'completion_heatmap': heatmap,
        })


class PomodoroAnalyticsView(APIView):
    """
    Pomodoro-specific analytics endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get pomodoro analytics",
        description="Get detailed focus session statistics.",
        tags=['Analytics'],
        parameters=[
            OpenApiParameter(
                name='days',
                description='Number of days to analyze',
                type=int,
                default=30
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_sessions': {'type': 'integer'},
                    'completed_sessions': {'type': 'integer'},
                    'total_focus_minutes': {'type': 'integer'},
                    'total_break_minutes': {'type': 'integer'},
                    'avg_session_duration': {'type': 'number'},
                    'avg_interruptions': {'type': 'number'},
                    'completion_rate': {'type': 'number'},
                    'sessions_by_hour': {'type': 'array'},
                    'sessions_by_day': {'type': 'array'},
                    'most_focused_tasks': {'type': 'array'},
                }
            }
        }
    )
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        sessions = PomodoroSession.objects.filter(
            user=user,
            start_time__gte=start_date
        )
        
        completed = sessions.filter(status='completed')
        focus_sessions = completed.filter(session_type='focus')
        break_sessions = completed.filter(session_type__in=['short_break', 'long_break'])
        
        # Aggregates
        total_focus = focus_sessions.aggregate(total=Sum('actual_duration'))['total'] or 0
        total_breaks = break_sessions.aggregate(total=Sum('actual_duration'))['total'] or 0
        avg_duration = focus_sessions.aggregate(avg=Avg('actual_duration'))['avg'] or 0
        avg_interruptions = focus_sessions.aggregate(avg=Avg('interruptions_count'))['avg'] or 0
        
        # By hour
        by_hour = list(
            focus_sessions
            .annotate(hour=ExtractHour('start_time'))
            .values('hour')
            .annotate(count=Count('id'), total_minutes=Sum('actual_duration'))
            .order_by('hour')
        )
        
        # By day
        by_day = list(
            focus_sessions
            .annotate(date=TruncDate('start_time'))
            .values('date')
            .annotate(count=Count('id'), total_minutes=Sum('actual_duration'))
            .order_by('date')
        )
        
        # Most focused tasks
        most_focused = list(
            focus_sessions
            .exclude(task__isnull=True)
            .values('task__id', 'task__title')
            .annotate(
                sessions=Count('id'),
                total_minutes=Sum('actual_duration')
            )
            .order_by('-total_minutes')[:10]
        )
        
        return Response({
            'total_sessions': sessions.count(),
            'completed_sessions': completed.count(),
            'total_focus_minutes': total_focus,
            'total_break_minutes': total_breaks,
            'avg_session_duration': round(avg_duration, 1),
            'avg_interruptions': round(avg_interruptions, 2),
            'completion_rate': round(
                (completed.count() / max(sessions.count(), 1)) * 100, 1
            ),
            'sessions_by_hour': by_hour,
            'sessions_by_day': [
                {
                    'date': item['date'].isoformat() if item['date'] else None,
                    'count': item['count'],
                    'total_minutes': item['total_minutes']
                }
                for item in by_day
            ],
            'most_focused_tasks': [
                {
                    'task_id': str(item['task__id']),
                    'title': item['task__title'],
                    'sessions': item['sessions'],
                    'total_minutes': item['total_minutes']
                }
                for item in most_focused
            ],
        })


class ProductivityTrendView(APIView):
    """
    Productivity trend analysis endpoint.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get productivity trends",
        description="Get historical productivity trends and insights.",
        tags=['Analytics'],
        parameters=[
            OpenApiParameter(
                name='period',
                description='Period to analyze: week, month, quarter',
                type=str,
                default='month'
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'period': {'type': 'string'},
                    'start_date': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'productivity_trend': {'type': 'array'},
                    'focus_time_trend': {'type': 'array'},
                    'avg_productivity_score': {'type': 'number'},
                    'productivity_change': {'type': 'number'},
                    'avg_daily_tasks': {'type': 'number'},
                    'avg_daily_focus_minutes': {'type': 'number'},
                    'insights': {'type': 'array'},
                    'recommendations': {'type': 'array'},
                }
            }
        }
    )
    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'month')
        
        # Determine date range
        if period == 'week':
            days = 7
        elif period == 'quarter':
            days = 90
        else:  # month
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)
        
        # Current period data
        current_tasks = Task.objects.filter(
            user=user,
            created_at__date__gte=start_date
        )
        current_completed = current_tasks.filter(status='completed').count()
        current_total = current_tasks.count()
        
        # Previous period for comparison
        prev_tasks = Task.objects.filter(
            user=user,
            created_at__date__gte=prev_start,
            created_at__date__lt=start_date
        )
        prev_completed = prev_tasks.filter(status='completed').count()
        prev_total = prev_tasks.count()
        
        # Calculate change
        current_rate = (current_completed / max(current_total, 1)) * 100
        prev_rate = (prev_completed / max(prev_total, 1)) * 100
        change = current_rate - prev_rate
        
        # Daily trends
        productivity_trend = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            day_tasks = Task.objects.filter(user=user, created_at__date=date)
            day_completed = day_tasks.filter(status='completed').count()
            day_total = day_tasks.count()
            
            productivity_trend.append({
                'date': date.isoformat(),
                'tasks_created': day_total,
                'tasks_completed': day_completed,
                'score': round((day_completed / max(day_total, 1)) * 100, 1)
            })
        
        # Focus time trend
        focus_trend = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            focus = PomodoroSession.objects.filter(
                user=user,
                start_time__date=date,
                status='completed',
                session_type='focus'
            ).aggregate(total=Sum('actual_duration'))['total'] or 0
            
            focus_trend.append({
                'date': date.isoformat(),
                'minutes': focus
            })
        
        # Generate insights
        insights = []
        
        avg_daily_tasks = current_total / days
        avg_focus_per_day = sum(f['minutes'] for f in focus_trend) / days
        
        if change > 10:
            insights.append({
                'type': 'positive',
                'message': f'Your completion rate improved by {round(change, 1)}% compared to the previous period!'
            })
        elif change < -10:
            insights.append({
                'type': 'negative',
                'message': f'Your completion rate decreased by {round(abs(change), 1)}%. Consider reviewing your task prioritization.'
            })
        
        if avg_focus_per_day > 120:
            insights.append({
                'type': 'positive',
                'message': f'Great focus time! You average {round(avg_focus_per_day)} minutes of focused work daily.'
            })
        
        # Recommendations
        recommendations = []
        if avg_focus_per_day < 60:
            recommendations.append('Try to schedule at least 2 pomodoro sessions per day for better focus.')
        if current_rate < 50:
            recommendations.append('Consider breaking down large tasks into smaller, more manageable pieces.')
        
        return Response({
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'productivity_trend': productivity_trend,
            'focus_time_trend': focus_trend,
            'avg_productivity_score': round(current_rate, 1),
            'productivity_change': round(change, 1),
            'avg_daily_tasks': round(avg_daily_tasks, 1),
            'avg_daily_focus_minutes': round(avg_focus_per_day, 1),
            'insights': insights,
            'recommendations': recommendations,
        })
