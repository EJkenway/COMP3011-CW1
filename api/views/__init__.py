"""
API Views Package

This package contains all views for the Smart Productivity Analytics Platform API.
"""

from .auth import (
    RegisterView,
    ProfileView,
    ChangePasswordView,
)
from .tasks import (
    CategoryViewSet,
    TagViewSet,
    TaskViewSet,
)
from .productivity import (
    PomodoroSessionViewSet,
    HabitViewSet,
)
from .analytics import (
    AnalyticsDashboardView,
    TaskAnalyticsView,
    HabitAnalyticsView,
    PomodoroAnalyticsView,
    ProductivityTrendView,
)
from .mcp import (
    MCPCapabilitiesView,
    MCPToolsView,
    MCPExecuteView,
)

__all__ = [
    # Auth
    'RegisterView',
    'ProfileView',
    'ChangePasswordView',
    # Tasks
    'CategoryViewSet',
    'TagViewSet',
    'TaskViewSet',
    # Productivity
    'PomodoroSessionViewSet',
    'HabitViewSet',
    # Analytics
    'AnalyticsDashboardView',
    'TaskAnalyticsView',
    'HabitAnalyticsView',
    'PomodoroAnalyticsView',
    'ProductivityTrendView',
    # MCP
    'MCPCapabilitiesView',
    'MCPToolsView',
    'MCPExecuteView',
]
