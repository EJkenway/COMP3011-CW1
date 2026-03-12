"""
API Views Package

This package contains all views for the Smart Productivity Analytics Platform API.
"""

from .auth import (
    RegisterView,
    ProfileView,
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenBlacklistView,
)
from .tasks import (
    CategoryViewSet,
    TagViewSet,
    TaskViewSet,
)
from .analytics import (
    AnalyticsDashboardView,
    TaskAnalyticsView,
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
    'CustomTokenObtainPairView',
    'CustomTokenRefreshView',
    'CustomTokenBlacklistView',
    # Tasks
    'CategoryViewSet',
    'TagViewSet',
    'TaskViewSet',
    # Analytics
    'AnalyticsDashboardView',
    'TaskAnalyticsView',
    'ProductivityTrendView',
    # MCP
    'MCPCapabilitiesView',
    'MCPToolsView',
    'MCPExecuteView',
]
