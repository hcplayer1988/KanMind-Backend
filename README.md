# KanMind - Kanban Board Backend

A Django REST Framework backend for a Kanban board application with user authentication, board management, task tracking, and comments.

## Features

- **User Authentication**: Email-based login with token authentication
- **Board Management**: Create, read, update, and delete boards
- **Multi-User Support**: Add members to boards with role-based permissions
- **Task Management**: Full CRUD operations for tasks with status tracking
- **Task Assignment**: Assign tasks to users and reviewers
- **Comments**: Add and manage comments on tasks
- **Filtering**: Filter tasks by assignee and reviewer
- **CORS Enabled**: Ready for frontend integration

## Tech Stack

- **Django 6.0.1**
- **Django REST Framework**
- **Token Authentication**
- **SQLite Database** (easily switchable to PostgreSQL/MySQL)
- **django-cors-headers** for CORS support

## Project Structure
```
KanMind/
├── core/                      # Main project settings
│   ├── settings.py
│   └── urls.py
├── authentikation/            # Authentication app
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── models.py             # CustomUser model
│   ├── backends.py           # Email authentication backend
│   └── admin.py
├── board/                     # Board management app
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── models.py             # Board model
│   └── admin.py
├── tasks/                     # Task management app
│   ├── api/
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── models.py             # Task and Comment models
│   └── admin.py
├── db.sqlite3                # SQLite database
├── manage.py
└── requirements.txt
```

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### 1. Clone the Repository
```bash
git clone 
cd KanMind
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Required packages:**
```
Django==6.0.1
djangorestframework
django-cors-headers
```

### 4. Database Setup
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 6. Start Development Server
```bash
python manage.py runserver
```

The API will be available at: `http://127.0.0.1:8000/`

## Configuration

### Important Settings

#### CORS Configuration (`core/settings.py`)

**CRITICAL**: Update `CORS_ALLOWED_ORIGINS` with your frontend URL:
```python
CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:5500',    # Update with your frontend URL
    'http://localhost:5500',     # Update with your frontend URL
]
```

#### Authentication Backend

The project uses **email-based authentication** instead of username:
```python
AUTHENTICATION_BACKENDS = [
    'authentikation.backends.EmailBackend',
]

AUTH_USER_MODEL = 'authentikation.CustomUser'
```

#### REST Framework Settings
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}
```

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/registration/` | Register new user | No |
| POST | `/api/login/` | Login and get token | No |
| GET | `/api/email-check/?email=<email>` | Check if email exists | Yes |

### Boards

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/boards/` | List all accessible boards | Yes |
| POST | `/api/boards/` | Create new board | Yes |
| GET | `/api/boards/{id}/` | Get board details | Yes (Member/Owner) |
| PATCH | `/api/boards/{id}/` | Update board | Yes (Member/Owner) |
| DELETE | `/api/boards/{id}/` | Delete board | Yes (Owner only) |

### Tasks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/tasks/assigned-to-me/` | Tasks assigned to current user | Yes |
| GET | `/api/tasks/reviewing/` | Tasks user is reviewing | Yes |
| POST | `/api/tasks/` | Create new task | Yes (Board member) |
| PATCH | `/api/tasks/{id}/` | Update task | Yes (Board member) |
| DELETE | `/api/tasks/{id}/` | Delete task | Yes (Board owner) |

### Comments

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/tasks/{task_id}/comments/` | Get all comments | Yes (Board member) |
| POST | `/api/tasks/{task_id}/comments/` | Create comment | Yes (Board member) |
| DELETE | `/api/tasks/{task_id}/comments/{comment_id}/` | Delete comment | Yes (Comment author) |

## API Usage Examples

### Registration
```bash
POST http://127.0.0.1:8000/api/registration/

{
  "fullname": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "repeated_password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "token": "9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b",
  "fullname": "John Doe",
  "email": "john@example.com",
  "user_id": 1
}
```

### Login
```bash
POST http://127.0.0.1:8000/api/login/

{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "token": "9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b",
  "fullname": "John Doe",
  "email": "john@example.com",
  "user_id": 1
}
```

### Create Board
```bash
POST http://127.0.0.1:8000/api/boards/
Authorization: Token 9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b

{
  "title": "Project X",
  "members": [2, 3, 4]
}
```

### Create Task
```bash
POST http://127.0.0.1:8000/api/tasks/
Authorization: Token 9d3a5f7b2c1e8d4f6a9b3c7e5d2a8f1b

{
  "board": 1,
  "title": "Implement login feature",
  "description": "Add email-based authentication",
  "status": "to-do",
  "priority": "high",
  "assignee_id": 2,
  "reviewer_id": 3,
  "due_date": "2026-02-15"
}
```

## Special Features & Considerations

### 1. Email-Based Authentication

- Users log in with **email and password** (not username)
- Username field accepts spaces and special characters
- Custom `EmailBackend` handles authentication

### 2. Task Status Values

**IMPORTANT**: Task status uses `'review'` (not `'reviewing'`)

Valid status values:
- `'to-do'`
- `'in-progress'`
- `'review'`
- `'done'`

### 3. Permissions System

- **Public endpoints**: Registration, Login
- **Authenticated endpoints**: All others require valid token
- **Board access**: Only owners and members can view/edit
- **Board deletion**: Only owner can delete
- **Task deletion**: Only board owner can delete
- **Comment deletion**: Only comment author can delete

### 4. CORS Configuration

**Browser Extensions**: Disable any "Allow CORS" browser extensions! They interfere with the built-in CORS configuration.

The backend has proper CORS headers configured. No browser extensions needed.

### 5. Frontend Integration

**Include token in all authenticated requests:**
```javascript
fetch('http://127.0.0.1:8000/api/boards/', {
  method: 'GET',
  headers: {
    'Authorization': 'Token YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  }
})
```

### 6. Database Reset

If you need to reset the database:
```bash
# Delete database
rm db.sqlite3

# Delete migrations (keep __init__.py!)
rm authentikation/migrations/0*.py
rm board/migrations/0*.py
rm tasks/migrations/0*.py

# Recreate database
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Admin Panel

Access the Django admin at: `http://127.0.0.1:8000/admin/`

**Features:**
- User management
- Board overview
- Task management
- Comment moderation

## Development

### Code Style

This project follows **PEP 8** style guidelines.

**Format code with:**
```bash
pip install black flake8 isort

# Format code
black .

# Sort imports
isort .

# Check for issues
flake8 .
```

### Testing
```bash
python manage.py test
```

## Troubleshooting

### Issue: CORS errors in browser

**Solution:**
1. Check `CORS_ALLOWED_ORIGINS` in settings.py
2. Disable browser CORS extensions
3. Clear browser cache (Ctrl + Shift + R)
4. Test in Incognito mode

### Issue: "Invalid email or password" despite correct credentials

**Solution:**
Database might have old data. Reset the password:
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='your@email.com')
user.set_password('your_password')
user.save()
```

### Issue: 401 Unauthorized on endpoints

**Solution:**
1. Check if token is valid
2. Ensure `Authorization: Token <token>` header is included
3. Verify token exists: `http://127.0.0.1:8000/admin/` → Auth Token → Tokens

### Issue: Migrations conflict

**Solution:**
```bash
python manage.py migrate --run-syncdb
```

Or reset database (see "Database Reset" section above).

## Production Deployment

### Before deploying:

1. **Change SECRET_KEY** in settings.py
2. **Set DEBUG = False**
3. **Configure ALLOWED_HOSTS**
4. **Use PostgreSQL/MySQL** instead of SQLite
5. **Set up proper static/media file serving**
6. **Use environment variables** for sensitive data
7. **Enable HTTPS**
8. **Configure proper logging**
```python
# Example production settings
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kanmind_db',
        'USER': 'db_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```


## Acknowledgments

- Django REST Framework
- django-cors-headers