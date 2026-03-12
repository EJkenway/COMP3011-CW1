"""
Django Admin Configuration for Core Models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Tag, Task


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
