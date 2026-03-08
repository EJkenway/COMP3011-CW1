"""
URL configuration for Smart Productivity Analytics Platform API.

API versioning: All API endpoints are prefixed with /api/v1/

Documentation:
- Swagger UI: /api/v1/docs/swagger/
- ReDoc: /api/v1/docs/redoc/
- OpenAPI Schema: /api/v1/docs/schema/
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    """API root endpoint with basic info."""
    return JsonResponse({
        'name': 'Smart Productivity Analytics Platform API',
        'version': '1.0.0',
        'documentation': {
            'swagger': '/api/v1/docs/swagger/',
            'redoc': '/api/v1/docs/redoc/',
            'openapi_schema': '/api/v1/docs/schema/',
        },
        'endpoints': {
            'auth': '/api/v1/auth/',
            'tasks': '/api/v1/tasks/',
            'categories': '/api/v1/categories/',
            'tags': '/api/v1/tags/',
            'habits': '/api/v1/habits/',
            'pomodoro': '/api/v1/pomodoro/',
            'analytics': '/api/v1/analytics/',
            'mcp': '/api/v1/mcp/',
        }
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API root
    path('', api_root, name='api_root'),
    
    # API v1
    path('api/v1/', include('api.urls')),
]
