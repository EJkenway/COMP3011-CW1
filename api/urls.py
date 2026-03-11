"""
API URL Configuration

Provides versioned API endpoints (api/v1/).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import (
    # Auth
    RegisterView,
    ProfileView,
    ChangePasswordView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenBlacklistView,
    # Tasks
    CategoryViewSet,
    TagViewSet,
    TaskViewSet,
    # Productivity
    PomodoroSessionViewSet,
    HabitViewSet,
    # Analytics
    AnalyticsDashboardView,
    TaskAnalyticsView,
    HabitAnalyticsView,
    PomodoroAnalyticsView,
    ProductivityTrendView,
    # MCP
    MCPCapabilitiesView,
    MCPToolsView,
    MCPExecuteView,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'pomodoro', PomodoroSessionViewSet, basename='pomodoro')
router.register(r'habits', HabitViewSet, basename='habit')

# Authentication URLs
auth_patterns = [
    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', CustomTokenBlacklistView.as_view(), name='token_blacklist'),
    
    # User management
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]

# Analytics URLs
analytics_patterns = [
    path('dashboard/', AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    path('tasks/', TaskAnalyticsView.as_view(), name='analytics_tasks'),
    path('habits/', HabitAnalyticsView.as_view(), name='analytics_habits'),
    path('pomodoro/', PomodoroAnalyticsView.as_view(), name='analytics_pomodoro'),
    path('trends/', ProductivityTrendView.as_view(), name='analytics_trends'),
]

# MCP (Model Context Protocol) URLs
mcp_patterns = [
    path('capabilities/', MCPCapabilitiesView.as_view(), name='mcp_capabilities'),
    path('tools/', MCPToolsView.as_view(), name='mcp_tools'),
    path('execute/', MCPExecuteView.as_view(), name='mcp_execute'),
]

# API v1 URL patterns
urlpatterns = [
    # Authentication
    path('auth/', include((auth_patterns, 'auth'))),
    
    # Core resources (router-based)
    path('', include(router.urls)),
    
    # Analytics
    path('analytics/', include((analytics_patterns, 'analytics'))),
    
    # MCP Integration
    path('mcp/', include((mcp_patterns, 'mcp'))),
    
    # Documentation (直接定义避免命名空间问题)
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
