"""
Core Data Models for Smart Productivity API

This module defines all database models for the task management system.
Features include:
- Custom User model with productivity preferences
- Task management with priority, categories, and time tracking
- Category and tag organization

Author: Student
Course: COMP3011 Web Services and Web Data
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
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
    
    # Subtask support
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks',
        help_text='Parent task for subtask hierarchy'
    )
    
    # Scheduling
    reminder_date = models.DateTimeField(null=True, blank=True)
    scheduled_date = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    location = models.CharField(max_length=255, blank=True)
    external_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True)

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
