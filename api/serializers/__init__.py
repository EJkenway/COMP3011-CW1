"""
API Serializers Package

This package contains all serializers for the Smart Productivity Analytics Platform API.
"""

from .auth import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from .tasks import (
    CategorySerializer,
    TagSerializer,
    TaskListSerializer,
    TaskDetailSerializer,
    TaskCreateUpdateSerializer,
)
from .productivity import (
    PomodoroSessionSerializer,
    PomodoroSessionCreateSerializer,
    HabitSerializer,
    HabitCreateUpdateSerializer,
    HabitLogSerializer,
    ProductivitySnapshotSerializer,
)
from .analytics import (
    DailyStatsSerializer,
    WeeklyStatsSerializer,
    ProductivityTrendSerializer,
)

__all__ = [
    # Auth
    'UserRegistrationSerializer',
    'UserSerializer',
    'UserProfileUpdateSerializer',
    'ChangePasswordSerializer',
    # Tasks
    'CategorySerializer',
    'TagSerializer',
    'TaskListSerializer',
    'TaskDetailSerializer',
    'TaskCreateUpdateSerializer',
    # Productivity
    'PomodoroSessionSerializer',
    'PomodoroSessionCreateSerializer',
    'HabitSerializer',
    'HabitCreateUpdateSerializer',
    'HabitLogSerializer',
    'ProductivitySnapshotSerializer',
    # Analytics
    'DailyStatsSerializer',
    'WeeklyStatsSerializer',
    'ProductivityTrendSerializer',
]
