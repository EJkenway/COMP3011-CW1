"""
Inline Serializers for API Documentation

These serializers are used with @extend_schema to provide clear request/response
documentation for action endpoints that don't use standard model serializers.
"""
from rest_framework import serializers


# =============================================================================
# Task Action Serializers
# =============================================================================

class BulkUpdateStatusRequestSerializer(serializers.Serializer):
    """Request body for bulk status update endpoint."""
    task_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of task UUIDs to update"
    )
    status = serializers.ChoiceField(
        choices=['pending', 'in_progress', 'completed', 'cancelled'],
        help_text="New status for the tasks"
    )


class BulkUpdateStatusResponseSerializer(serializers.Serializer):
    """Response for bulk status update endpoint."""
    updated_count = serializers.IntegerField(help_text="Number of tasks updated")
    message = serializers.CharField(help_text="Success message")


# =============================================================================
# Pomodoro Action Serializers
# =============================================================================

class PomodoroCompleteRequestSerializer(serializers.Serializer):
    """Request body for completing a pomodoro session."""
    interruptions_count = serializers.IntegerField(
        required=False,
        default=0,
        help_text="Number of interruptions during the session"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes about the session"
    )


# =============================================================================
# Habit Action Serializers
# =============================================================================

class HabitCompleteRequestSerializer(serializers.Serializer):
    """Request body for logging a habit completion."""
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional notes about this completion"
    )


class HabitCompleteResponseSerializer(serializers.Serializer):
    """Response for habit completion endpoint."""
    log = serializers.DictField(help_text="The created log entry")
    habit = serializers.DictField(help_text="Updated habit data with new streak")
    message = serializers.CharField(help_text="Success message with streak info")


# =============================================================================
# MCP Action Serializers
# =============================================================================

class MCPExecuteRequestSerializer(serializers.Serializer):
    """Request body for MCP tool execution."""
    tool = serializers.CharField(help_text="Name of the tool to execute")
    arguments = serializers.DictField(
        required=False,
        default=dict,
        help_text="Arguments for the tool"
    )


class MCPExecuteResponseSerializer(serializers.Serializer):
    """Response for MCP tool execution."""
    success = serializers.BooleanField(help_text="Whether the execution was successful")
    result = serializers.DictField(
        required=False,
        allow_null=True,
        help_text="Result data from the tool execution"
    )
    error = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Error message if execution failed"
    )
