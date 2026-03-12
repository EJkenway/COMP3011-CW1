"""
Analytics and Statistics Serializers
"""
from rest_framework import serializers


class DailyStatsSerializer(serializers.Serializer):
    """
    Serializer for daily productivity statistics.
    
    Aggregated data for a single day.
    """
    date = serializers.DateField()
    tasks_created = serializers.IntegerField()
    tasks_completed = serializers.IntegerField()
    tasks_pending = serializers.IntegerField()
    tasks_overdue = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    productivity_score = serializers.FloatField()
    most_productive_hour = serializers.IntegerField(allow_null=True)
    top_categories = serializers.ListField(
        child=serializers.DictField()
    )


class WeeklyStatsSerializer(serializers.Serializer):
    """
    Serializer for weekly productivity statistics.
    
    Aggregated data with daily breakdown.
    """
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    total_tasks_created = serializers.IntegerField()
    total_tasks_completed = serializers.IntegerField()
    avg_completion_rate = serializers.FloatField()
    avg_productivity_score = serializers.FloatField()
    best_day = serializers.DictField()
    daily_breakdown = serializers.ListField(
        child=serializers.DictField()
    )
    category_distribution = serializers.ListField(
        child=serializers.DictField()
    )
    priority_distribution = serializers.DictField()


class ProductivityTrendSerializer(serializers.Serializer):
    """
    Serializer for productivity trend analysis.
    
    Historical data for trend visualization.
    """
    period = serializers.CharField()  # 'week', 'month', 'quarter'
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    # Trend metrics
    productivity_trend = serializers.ListField(
        child=serializers.DictField()
    )
    completion_trend = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Summary statistics
    avg_productivity_score = serializers.FloatField()
    productivity_change = serializers.FloatField()  # % change from previous period
    avg_daily_tasks = serializers.FloatField()
    
    # Insights
    insights = serializers.ListField(
        child=serializers.DictField()
    )
    recommendations = serializers.ListField(
        child=serializers.CharField()
    )


class TaskAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for task-specific analytics.
    """
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    
    avg_completion_time_minutes = serializers.FloatField(allow_null=True)
    avg_estimated_vs_actual = serializers.FloatField(allow_null=True)
    
    by_priority = serializers.DictField()
    by_energy_level = serializers.DictField()
    by_category = serializers.ListField(
        child=serializers.DictField()
    )
    
    completion_by_hour = serializers.ListField(
        child=serializers.DictField()
    )
    completion_by_day = serializers.ListField(
        child=serializers.DictField()
    )
