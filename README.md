# Smart Productivity Analytics Platform API

A comprehensive RESTful API for intelligent task management, habit tracking, Pomodoro timer, and productivity analytics. Features Model Context Protocol (MCP) integration for AI agent interoperability.

## Project Overview

| Item | Description |
|------|-------------|
| **Name** | Smart Productivity Analytics Platform |
| **Purpose** | Provide a comprehensive productivity management API with AI integration capabilities |
| **Core Features** | Task CRUD, Habit Tracking, Pomodoro Timer, Analytics Dashboard, MCP Integration |
| **API Version** | v1 |
| **Auth Method** | JWT (JSON Web Token) |

## Features

### Task Management
- Full CRUD operations with filtering, searching, and sorting
- Categories (hierarchical) and Tags (many-to-many)
- Priority levels (1-5) and energy levels (low/medium/high)
- Subtask support via parent-child relationships
- Bulk status updates and custom actions (complete, reopen)

### Habit Tracking
- Daily, weekly, and monthly frequency options
- Automatic streak calculation (current and best)
- Completion logging with notes
- History retrieval for analytics

### Pomodoro Timer
- Focus sessions with configurable duration
- Short and long break management
- Interruption counting
- Task association for time tracking

### Analytics
- Dashboard with today/weekly summaries
- Task completion rates and trends
- Habit performance analysis
- Productivity insights by time of day

### MCP Integration
- Model Context Protocol compatible endpoints
- Tool discovery with JSON Schema definitions
- Programmable execution for AI agents
- Smart task suggestions based on energy level

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Django | 5.2 |
| API Layer | Django REST Framework | 3.15 |
| Authentication | Simple JWT | 5.3 |
| Documentation | drf-spectacular | 0.28 |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| Testing | pytest-django | 4.5 |
| Filtering | django-filter | 24.3 |

## Code Structure

```
todo_api/
├── api/                      # API application
│   ├── views/               # ViewSets and APIViews
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── tasks.py        # Task/Category/Tag endpoints
│   │   ├── productivity.py # Habit/Pomodoro endpoints
│   │   ├── analytics.py    # Analytics endpoints
│   │   └── mcp.py          # MCP integration endpoints
│   ├── serializers/         # Request/Response serialization
│   │   ├── auth.py
│   │   ├── tasks.py
│   │   └── productivity.py
│   └── urls.py              # URL routing with versioning
├── core/                     # Core business logic
│   ├── models.py            # Data models (User, Task, Habit, etc.)
│   └── admin.py             # Django admin configuration
├── tests/                    # Test suite (57 tests)
│   ├── conftest.py          # Shared fixtures
│   ├── test_auth.py         # Authentication tests
│   ├── test_tasks.py        # Task CRUD tests
│   ├── test_productivity.py # Habit/Pomodoro tests
│   └── test_mcp.py          # MCP integration tests
├── requirements.txt          # Python dependencies
└── todo_api/                 # Project configuration
    ├── settings.py          # Django settings
    └── urls.py              # Root URL configuration
```

## Installation

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create logs directory
mkdir -p logs

# 4. Apply database migrations
python manage.py migrate

# 5. Create superuser (optional, for admin access)
python manage.py createsuperuser

# 6. Start development server
python manage.py runserver
```

Server runs at `http://localhost:8000/`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key for cryptographic signing | (insecure dev default) |
| `DJANGO_DEBUG` | Enable debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | SQLite |

## API Documentation

| Type | URL | Description |
|------|-----|-------------|
| Swagger UI | http://localhost:8000/api/v1/docs/swagger/ | Interactive API explorer |
| ReDoc | http://localhost:8000/api/v1/docs/redoc/ | Clean API reference |
| OpenAPI Schema | http://localhost:8000/api/v1/docs/schema/ | Raw JSON/YAML schema |
| Admin Panel | http://localhost:8000/admin/ | Data management interface |

## API Endpoints Overview

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Auth | 6 | Register, login, token refresh, profile, password change |
| Tasks | 11 | CRUD, complete, reopen, today, overdue, bulk update |
| Categories | 7 | CRUD with statistics |
| Tags | 6 | CRUD operations |
| Habits | 8 | CRUD, complete, history |
| Pomodoro | 8 | CRUD, complete, cancel, active, summary |
| Analytics | 5 | Dashboard, task/habit/pomodoro analytics, trends |
| MCP | 3 | Capabilities, tools, execute |

## curl Examples

Below are curl examples organized by functionality. Each section shows the most common operations.

### Authentication

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

**Login (obtain JWT tokens):**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

**Refresh access token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

### Tasks

**Create a task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project report",
    "description": "Write the final section",
    "priority": 4,
    "energy_level": "high",
    "due_date": "2026-03-15T17:00:00Z"
  }'
```

**List tasks with filtering:**
```bash
# Filter by status and priority
curl "http://localhost:8000/api/v1/tasks/?status=pending&priority=4" \
  -H "Authorization: Bearer <access_token>"

# Get today's tasks
curl http://localhost:8000/api/v1/tasks/today/ \
  -H "Authorization: Bearer <access_token>"

# Get overdue tasks
curl http://localhost:8000/api/v1/tasks/overdue/ \
  -H "Authorization: Bearer <access_token>"
```

**Complete a task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/<task_id>/complete/ \
  -H "Authorization: Bearer <access_token>"
```

### Habits

**Create a habit:**
```bash
curl -X POST http://localhost:8000/api/v1/habits/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning meditation",
    "description": "10 minutes of mindfulness",
    "frequency": "daily",
    "target_count": 1
  }'
```

**Log habit completion:**
```bash
curl -X POST http://localhost:8000/api/v1/habits/<habit_id>/complete/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Completed 15 minutes today"}'
```

### Pomodoro

**Start a focus session:**
```bash
curl -X POST http://localhost:8000/api/v1/pomodoro/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "focus",
    "planned_duration": 25,
    "task": "<task_id>"
  }'
```

**Complete a session:**
```bash
curl -X POST http://localhost:8000/api/v1/pomodoro/<session_id>/complete/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"interruptions_count": 2, "notes": "Stayed focused"}'
```

### Analytics

**Get dashboard overview:**
```bash
curl http://localhost:8000/api/v1/analytics/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```

**Get task analytics (last 30 days):**
```bash
curl "http://localhost:8000/api/v1/analytics/tasks/?days=30" \
  -H "Authorization: Bearer <access_token>"
```

### MCP (Model Context Protocol)

**Discover API capabilities (public):**
```bash
curl http://localhost:8000/api/v1/mcp/capabilities/
```

**List available tools:**
```bash
curl http://localhost:8000/api/v1/mcp/tools/ \
  -H "Authorization: Bearer <access_token>"
```

**Execute a tool - Smart task suggestion:**
```bash
curl -X POST http://localhost:8000/api/v1/mcp/execute/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "suggest_next_task",
    "arguments": {"energy_level": "low"}
  }'
```

**Execute a tool - Create task via MCP:**
```bash
curl -X POST http://localhost:8000/api/v1/mcp/execute/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_task",
    "arguments": {
      "title": "Review pull requests",
      "priority": "high"
    }
  }'
```

## Testing

```bash
# Run all tests (57 tests)
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=api --cov=core --cov-report=html

# Run specific test modules
pytest tests/test_auth.py -v      # Authentication tests
pytest tests/test_tasks.py -v     # Task CRUD tests
pytest tests/test_mcp.py -v       # MCP integration tests

# Run tests matching a pattern
pytest -k "test_create" -v
```

## Deployment

```bash
# Set production environment variables
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY="your-production-secret-key"
export DJANGO_ALLOWED_HOSTS="your-domain.com,www.your-domain.com"

# Collect static files
python manage.py collectstatic --noinput

# Apply migrations
python manage.py migrate

# Run with gunicorn (production WSGI server)
gunicorn todo_api.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

## Security Features

- JWT authentication with 60-minute access token expiry
- Refresh token rotation and blacklisting
- Password strength validation
- Rate limiting (100/hour anonymous, 1000/hour authenticated)
- User data isolation (queryset filtering)

## License

MIT License
