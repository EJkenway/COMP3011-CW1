"""
Core Data Models for Smart Productivity API

This module defines all database models for the todo/productivity tracking system.
Features include:
- Custom User model with productivity preferences
- Task management with priority, categories, and time tracking
- Habit tracking with streaks
- Pomodoro sessions
- Productivity analytics snapshots

Author: Student
Course: COMP3011 Web Services and Web Data
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Extended User model with productivity-related preferences.
    Inherits from Django's AbstractUser for full authentication support.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    timezone = models.CharField(max_length=50, default='UTC')
    preferred_work_start = models.TimeField(default='09:00')
    preferred_work_end = models.TimeField(default='17:00')
    daily_task_goal = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class Category(models.Model):
    """
    Task categories with hierarchical support.
    Allows users to organize tasks into custom categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    icon = models.CharField(max_length=50, default='folder')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        unique_together = ['user', 'name', 'parent']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Tag(models.Model):
    """
    Flexible tagging system for tasks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6B7280')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tags'
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Core Task model with comprehensive tracking features.
    
    Supports:
    - Priority levels (1-5)
    - Status workflow (pending -> in_progress -> completed/archived)
    - Time estimation and actual tracking
    - Energy level tracking for productivity analysis
    - Category and tag organization
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    class EnergyLevel(models.TextChoices):
        HIGH = 'high', 'High Energy'
        MEDIUM = 'medium', 'Medium Energy'
        LOW = 'low', 'Low Energy'

    class Priority(models.IntegerChoices):
        LOWEST = 1, 'Lowest'
        LOW = 2, 'Low'
        MEDIUM = 3, 'Medium'
        HIGH = 4, 'High'
        HIGHEST = 5, 'Highest'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    
    # Basic info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Organization
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='tasks'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    
    # Status and priority
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    priority = models.IntegerField(
        choices=Priority.choices, 
        default=Priority.MEDIUM
    )
    
    # Time tracking
    due_date = models.DateTimeField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Estimated time to complete in minutes'
    )
    actual_minutes = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text='Actual time spent in minutes'
    )
    
    # Productivity tracking
    energy_level = models.CharField(
        max_length=10, 
        choices=EnergyLevel.choices, 
        default=EnergyLevel.MEDIUM,
        help_text='User energy level when creating task'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Recurrence (for habits)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)  # e.g., 'daily', 'weekly:mon,wed,fri'

    class Meta:
        db_table = 'tasks'
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'due_date']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-update timestamps based on status changes
        if self.status == self.Status.IN_PROGRESS and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if task is past due date."""
        if self.due_date and self.status not in [self.Status.COMPLETED, self.Status.ARCHIVED]:
            return timezone.now() > self.due_date
        return False

    @property
    def completion_time_minutes(self):
        """Calculate actual completion time if task is completed."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None


class PomodoroSession(models.Model):
    """
    Pomodoro technique session tracking.
    Tracks focus sessions with interruptions and notes.
    """
    
    class SessionType(models.TextChoices):
        FOCUS = 'focus', 'Focus Session'
        SHORT_BREAK = 'short_break', 'Short Break'
        LONG_BREAK = 'long_break', 'Long Break'

    class SessionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pomodoro_sessions')
    task = models.ForeignKey(
        Task, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pomodoro_sessions'
    )
    
    session_type = models.CharField(
        max_length=20, 
        choices=SessionType.choices, 
        default=SessionType.FOCUS
    )
    status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.ACTIVE
    )
    
    # Duration settings (in minutes)
    planned_duration = models.PositiveIntegerField(default=25)
    actual_duration = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    pause_time = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    interruptions_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'pomodoro_sessions'
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.session_type} - {self.user.username} ({self.start_time})"

    def complete(self):
        """Mark session as completed and calculate actual duration."""
        self.status = self.SessionStatus.COMPLETED
        self.end_time = timezone.now()
        delta = self.end_time - self.start_time
        self.actual_duration = int(delta.total_seconds() / 60)
        self.save()


class Habit(models.Model):
    """
    Habit tracking with streak calculation.
    Links to tasks for integrated habit-task workflow.
    """
    
    class Frequency(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        CUSTOM = 'custom', 'Custom'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    frequency = models.CharField(
        max_length=20, 
        choices=Frequency.choices, 
        default=Frequency.DAILY
    )
    
    # For weekly/custom frequency
    target_days = models.JSONField(
        default=list,
        help_text='Days of week for habit (0=Monday, 6=Sunday)'
    )
    target_count = models.PositiveIntegerField(
        default=1,
        help_text='Number of times to complete per period'
    )
    
    # Streak tracking
    current_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_completed = models.DateField(null=True, blank=True)
    
    # Statistics
    total_completions = models.PositiveIntegerField(default=0)
    
    # Settings
    reminder_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'habits'
        ordering = ['-current_streak', 'name']

    def __str__(self):
        return f"{self.name} (Streak: {self.current_streak})"

    def record_completion(self):
        """Record a habit completion and update streaks."""
        today = timezone.now().date()
        
        if self.last_completed == today:
            return  # Already completed today
        
        # Check if streak continues
        if self.last_completed:
            days_diff = (today - self.last_completed).days
            if days_diff == 1:
                self.current_streak += 1
            elif days_diff > 1:
                self.current_streak = 1  # Reset streak
        else:
            self.current_streak = 1
        
        # Update best streak
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
        
        self.last_completed = today
        self.total_completions += 1
        self.save()


class HabitLog(models.Model):
    """
    Individual habit completion logs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    completed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'habit_logs'
        ordering = ['-completed_at']


class ProductivitySnapshot(models.Model):
    """
    Daily productivity metrics snapshot.
    Used for analytics and trend analysis.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productivity_snapshots')
    date = models.DateField()
    
    # Task metrics
    tasks_created = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_overdue = models.PositiveIntegerField(default=0)
    
    # Time metrics
    total_focus_minutes = models.PositiveIntegerField(default=0)
    total_pomodoros_completed = models.PositiveIntegerField(default=0)
    avg_task_duration_minutes = models.FloatField(null=True, blank=True)
    
    # Productivity patterns
    peak_productivity_hour = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    energy_pattern = models.JSONField(
        default=dict,
        help_text='Hourly energy/productivity distribution'
    )
    
    # External data (weather integration)
    weather_condition = models.CharField(max_length=50, blank=True)
    temperature_celsius = models.FloatField(null=True, blank=True)
    
    # Habits
    habits_completed = models.PositiveIntegerField(default=0)
    habits_total = models.PositiveIntegerField(default=0)
    
    # Scores
    productivity_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'productivity_snapshots'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def calculate_productivity_score(self):
        """
        Calculate daily productivity score (0-100).
        Based on task completion, focus time, and habit adherence.
        """
        score = 0
        weights = {
            'task_completion': 40,
            'focus_time': 30,
            'habit_adherence': 30
        }
        
        # Task completion score
        if self.tasks_created > 0:
            completion_rate = self.tasks_completed / self.tasks_created
            score += completion_rate * weights['task_completion']
        
        # Focus time score (target: 4 hours = 240 minutes)
        focus_score = min(self.total_focus_minutes / 240, 1)
        score += focus_score * weights['focus_time']
        
        # Habit adherence
        if self.habits_total > 0:
            habit_rate = self.habits_completed / self.habits_total
            score += habit_rate * weights['habit_adherence']
        
        self.productivity_score = round(score, 2)
        return self.productivity_score
