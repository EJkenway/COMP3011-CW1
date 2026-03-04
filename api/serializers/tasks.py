"""
Task, Category, and Tag Serializers
"""
from rest_framework import serializers
from core.models import Category, Tag, Task


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for task categories.
    
    Supports hierarchical categories with parent-child relationships.
    """
    tasks_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon',
            'parent', 'is_active', 'tasks_count', 'subcategories',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tasks_count(self, obj):
        """Get number of tasks in this category."""
        return obj.tasks.count()
    
    def get_subcategories(self, obj):
        """Get child categories (one level deep)."""
        children = obj.subcategories.filter(is_active=True)
        return CategorySimpleSerializer(children, many=True).data
    
    def validate_parent(self, value):
        """Prevent circular references and deep nesting."""
        if value:
            # Check for circular reference
            if self.instance and value.id == self.instance.id:
                raise serializers.ValidationError(
                    "A category cannot be its own parent."
                )
            # Limit nesting depth to 2 levels
            if value.parent is not None:
                raise serializers.ValidationError(
                    "Categories can only be nested two levels deep."
                )
        return value
    
    def create(self, validated_data):
        """Create category with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CategorySimpleSerializer(serializers.ModelSerializer):
    """Simplified category serializer for nested display."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'icon']


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for task tags.
    
    Flexible tagging system for organizing tasks.
    """
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'tasks_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_tasks_count(self, obj):
        """Get number of tasks with this tag."""
        return obj.tasks.count()
    
    def create(self, validated_data):
        """Create tag with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_name(self, value):
        """Ensure tag name is unique for the user."""
        user = self.context['request'].user
        queryset = Tag.objects.filter(user=user, name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "You already have a tag with this name."
            )
        return value


class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for task list display.
    
    Optimized for list views with minimal data.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'priority', 'energy_level',
            'category', 'category_name', 'tags', 'due_date',
            'is_overdue', 'estimated_minutes', 'actual_minutes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_overdue']


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for task detail display.
    
    Full task data including all relationships.
    """
    category = CategorySimpleSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    total_pomodoro_minutes = serializers.SerializerMethodField()
    pomodoro_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'energy_level', 'category', 'tags', 'parent_task',
            'due_date', 'reminder_date', 'scheduled_date',
            'estimated_minutes', 'actual_minutes', 'is_overdue',
            'total_pomodoro_minutes', 'pomodoro_sessions_count',
            'location', 'external_url', 'notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'completed_at',
            'is_overdue', 'total_pomodoro_minutes', 'pomodoro_sessions_count'
        ]
    
    def get_total_pomodoro_minutes(self, obj):
        """Get total focus time from pomodoro sessions."""
        sessions = obj.pomodoro_sessions.filter(status='completed')
        return sum(s.actual_duration or 0 for s in sessions)
    
    def get_pomodoro_sessions_count(self, obj):
        """Get number of completed pomodoro sessions."""
        return obj.pomodoro_sessions.filter(status='completed').count()


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for task creation and updates.
    
    Handles tag assignment and validation.
    """
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'energy_level', 'category', 'tags', 'parent_task',
            'due_date', 'reminder_date', 'scheduled_date',
            'estimated_minutes', 'actual_minutes',
            'location', 'external_url', 'notes'
        ]
    
    def validate_category(self, value):
        """Ensure category belongs to current user."""
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError(
                "Invalid category - must belong to you."
            )
        return value
    
    def validate_tags(self, value):
        """Ensure all tags belong to current user."""
        user = self.context['request'].user
        for tag in value:
            if tag.user != user:
                raise serializers.ValidationError(
                    "Invalid tag - must belong to you."
                )
        return value
    
    def validate_parent_task(self, value):
        """Validate parent task relationships."""
        if value:
            user = self.context['request'].user
            if value.user != user:
                raise serializers.ValidationError(
                    "Parent task must belong to you."
                )
            # Prevent self-reference
            if self.instance and value.id == self.instance.id:
                raise serializers.ValidationError(
                    "A task cannot be its own parent."
                )
            # Prevent circular references
            if self.instance:
                current = value
                while current:
                    if current.id == self.instance.id:
                        raise serializers.ValidationError(
                            "Circular task reference detected."
                        )
                    current = current.parent_task
        return value
    
    def create(self, validated_data):
        """Create task with current user."""
        tags = validated_data.pop('tags', [])
        validated_data['user'] = self.context['request'].user
        task = Task.objects.create(**validated_data)
        task.tags.set(tags)
        return task
    
    def update(self, instance, validated_data):
        """Update task and handle tag assignment."""
        tags = validated_data.pop('tags', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags is not None:
            instance.tags.set(tags)
        
        return instance
