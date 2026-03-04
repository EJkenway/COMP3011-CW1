"""
Productivity Feature Serializers (Pomodoro, Habits, Snapshots)
"""
from rest_framework import serializers
from django.utils import timezone
from core.models import PomodoroSession, Habit, HabitLog, ProductivitySnapshot


class PomodoroSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for pomodoro session display.
    
    Shows full session details including task association.
    """
    task_title = serializers.CharField(source='task.title', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PomodoroSession
        fields = [
            'id', 'task', 'task_title', 'session_type', 'status',
            'planned_duration', 'actual_duration', 'duration_display',
            'start_time', 'end_time', 'interruptions', 'notes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'end_time', 'actual_duration']
    
    def get_duration_display(self, obj):
        """Human-readable duration string."""
        if obj.actual_duration:
            hours, remainder = divmod(obj.actual_duration, 60)
            if hours:
                return f"{hours}h {remainder}m"
            return f"{remainder}m"
        return f"{obj.planned_duration}m (planned)"


class PomodoroSessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating pomodoro sessions.
    
    Handles session initialization and validation.
    """
    class Meta:
        model = PomodoroSession
        fields = [
            'task', 'session_type', 'planned_duration', 'notes'
        ]
    
    def validate_task(self, value):
        """Ensure task belongs to current user."""
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError(
                "Task must belong to you."
            )
        return value
    
    def validate_planned_duration(self, value):
        """Validate duration is reasonable."""
        if value < 1:
            raise serializers.ValidationError(
                "Duration must be at least 1 minute."
            )
        if value > 180:
            raise serializers.ValidationError(
                "Duration cannot exceed 180 minutes."
            )
        return value
    
    def create(self, validated_data):
        """Create pomodoro session with current user and start time."""
        validated_data['user'] = self.context['request'].user
        validated_data['start_time'] = timezone.now()
        validated_data['status'] = 'in_progress'
        return super().create(validated_data)


class HabitLogSerializer(serializers.ModelSerializer):
    """
    Serializer for habit log entries.
    
    Simple record of habit completions.
    """
    class Meta:
        model = HabitLog
        fields = ['id', 'completed_at', 'notes']
        read_only_fields = ['id', 'completed_at']


class HabitSerializer(serializers.ModelSerializer):
    """
    Serializer for habit display.
    
    Shows habit details and streak information.
    """
    recent_completions = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Habit
        fields = [
            'id', 'name', 'description', 'frequency', 'target_count',
            'color', 'icon', 'reminder_time', 'current_streak',
            'best_streak', 'last_completed', 'is_active',
            'recent_completions', 'completion_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_streak', 'best_streak', 'last_completed',
            'created_at', 'updated_at'
        ]
    
    def get_recent_completions(self, obj):
        """Get last 7 completion records."""
        logs = obj.logs.order_by('-completed_at')[:7]
        return HabitLogSerializer(logs, many=True).data
    
    def get_completion_rate(self, obj):
        """Calculate completion rate for the last 30 days."""
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        completions = obj.logs.filter(completed_at__gte=thirty_days_ago).count()
        
        # Expected completions based on frequency
        if obj.frequency == 'daily':
            expected = 30 * obj.target_count
        elif obj.frequency == 'weekly':
            expected = 4 * obj.target_count  # ~4 weeks
        elif obj.frequency == 'monthly':
            expected = obj.target_count
        else:
            expected = 30  # Custom - assume daily
        
        if expected == 0:
            return 0
        
        return min(100, round((completions / expected) * 100, 1))


class HabitCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating habits.
    """
    class Meta:
        model = Habit
        fields = [
            'name', 'description', 'frequency', 'target_count',
            'color', 'icon', 'reminder_time', 'is_active'
        ]
    
    def validate_target_count(self, value):
        """Ensure target count is valid."""
        if value < 1:
            raise serializers.ValidationError(
                "Target count must be at least 1."
            )
        if value > 100:
            raise serializers.ValidationError(
                "Target count cannot exceed 100."
            )
        return value
    
    def create(self, validated_data):
        """Create habit with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductivitySnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer for daily productivity snapshots.
    
    Comprehensive daily summary data.
    """
    day_of_week = serializers.SerializerMethodField()
    weather_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductivitySnapshot
        fields = [
            'id', 'date', 'day_of_week', 'tasks_created', 'tasks_completed',
            'tasks_overdue', 'total_focus_minutes', 'pomodoro_sessions',
            'habits_completed', 'productivity_score', 'energy_level_avg',
            'most_productive_hour', 'weather_condition', 'weather_temperature',
            'weather_summary', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'date', 'created_at']
    
    def get_day_of_week(self, obj):
        """Get day name."""
        return obj.date.strftime('%A')
    
    def get_weather_summary(self, obj):
        """Formatted weather summary."""
        if obj.weather_condition and obj.weather_temperature:
            return f"{obj.weather_condition}, {obj.weather_temperature}°C"
        return None
