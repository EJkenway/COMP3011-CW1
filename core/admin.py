"""
Django Admin Configuration for Core Models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Category, Tag, Task, 
    PomodoroSession, Habit, HabitLog, 
    ProductivitySnapshot
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'timezone', 'daily_task_goal', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_staff', 'timezone']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Productivity Settings', {
            'fields': ('timezone', 'preferred_work_start', 'preferred_work_end', 'daily_task_goal')
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__email']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'created_at']
    search_fields = ['name', 'user__email']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'priority', 'category', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'energy_level', 'created_at']
    search_fields = ['title', 'description', 'user__email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(PomodoroSession)
class PomodoroSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'session_type', 'status', 'planned_duration', 'actual_duration', 'start_time']
    list_filter = ['session_type', 'status', 'start_time']
    search_fields = ['user__email', 'task__title']


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'frequency', 'current_streak', 'best_streak', 'is_active']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'user__email']


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ['habit', 'completed_at']
    list_filter = ['completed_at']


@admin.register(ProductivitySnapshot)
class ProductivitySnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tasks_completed', 'total_focus_minutes', 'productivity_score']
    list_filter = ['date']
    search_fields = ['user__email']
    date_hierarchy = 'date'
