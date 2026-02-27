# Home Server

A modular FastAPI home server with MongoDB backend, OAuth authentication (GitHub, Google, Microsoft), header-based authentication (Databricks, Azure App Service), and HTMX + Tailwind CSS frontend.

Please check and maintain docs/ for app specified architecture and design decision.

## Features

- **Modular Architecture**: Independent features with separate schemas, models, and routers
- **MongoDB + Motor**: Async MongoDB integration using motor
- **OAuth Authentication**: Support for GitHub, Google, and Microsoft OAuth providers
- **Header-Based Authentication**: Databricks App Service and Azure App Service support
- **HTMX + Tailwind CSS**: Server-rendered UI with interactive components
- **Auto-Discovery**: Features automatically discovered and registered
- **Landing Page**: Beautiful public landing page with login modal

## Project Structure

```
.
├── app/                    # Main application package
│   ├── auth/              # Authentication module
│   │   ├── providers.py   # OAuth provider registry
│   │   ├── github.py      # GitHub OAuth
│   │   ├── google.py      # Google OAuth
│   │   ├── microsoft.py   # Microsoft OAuth
│   │   ├── router.py      # Auth routes
│   │   ├── middleware.py  # Auth middleware (get_current_user)
│   │   ├── header_auth.py # Header-based auth (Databricks, Azure)
│   │   ├── user_service.py # Shared user creation service
│   │   └── schemas.py     # Auth Pydantic schemas
│   ├── core/              # Core application components
│   │   ├── config.py      # App configuration
│   │   ├── database.py    # MongoDB connection
│   │   ├── security.py   # JWT utilities
│   │   ├── features.py   # Feature auto-discovery
│   │   └── collections.py # MongoDB collection helpers
│   ├── models/            # MongoDB document schemas
│   │   ├── base.py       # Base model with common fields
│   │   ├── user.py       # User model
│   │   └── feature.py    # Feature model
│   ├── schemas/           # Pydantic schemas
│   │   └── base.py       # Base schemas
│   ├── features/          # Modular features
│   │   └── todos/       # Todo List feature
│   │       ├── model.py  # MongoDB model
│   │       ├── schema.py # Pydantic schemas
│   │       └── router.py # Routes (with feature_info)
│   └── templates/         # Jinja2 templates
│       ├── base.html     # Base template with HTMX + Tailwind
│       ├── landing.html  # Public landing page (no auth required)
│       ├── auth/
│       │   └── login.html # Login page (fallback)
│       ├── dashboard/
│       │   └── dashboard.html
│       └── components/
│           └── sidebar.html
├── tests/                 # Test files
│   └── test_header_auth.py
├── docs/                  # Documentation
│   ├── README.md          # Documentation index
│   ├── HEADER_AUTH.md     # Header authentication guide
│   └── MONGODB_PATTERNS.md # MongoDB patterns guide
├── main.py                # Application entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
└── .gitignore            # Git ignore rules
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=home_server

# OAuth Providers (at least one required for login)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

# Header-based Authentication (optional)
HEADER_AUTH_ENABLED=true
DATABRICKS_HEADER_AUTH=true
AZURE_APP_SERVICE_AUTH=true
TRUSTED_HEADER_PROXIES=127.0.0.1,::1

FRONTEND_URL=http://localhost:8001
```

### 3. Run MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or use your existing MongoDB instance
```

### 4. Start Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 5. Access the App

- **Root URL** (`http://localhost:8001`): Public landing page (no auth required)
- **Dashboard** (when authenticated): Shows your features
- **Login**: Click "Sign In" on landing page to open login modal

## Authentication

### OAuth Providers

#### GitHub
1. Go to https://github.com/settings/developers
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8001/auth/callback/github`
4. Copy Client ID and Client Secret

#### Google
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Google OAuth API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:8001/auth/callback/google` as authorized redirect URI

#### Microsoft
1. Go to https://portal.azure.com/
2. Register a new application
3. Add a platform -> Web
4. Set Redirect URI: `http://localhost:8001/auth/callback/microsoft`
5. Copy Application (client) ID and client secret

### Header-Based Authentication

Enable header-based auth for internal services (Databricks, Azure App Service):

```env
HEADER_AUTH_ENABLED=true
DATABRICKS_HEADER_AUTH=true
AZURE_APP_SERVICE_AUTH=true
TRUSTED_HEADER_PROXIES=127.0.0.1,::1
```

The server will automatically extract user info from:
- **Databricks**: `X-Databricks-User-Email` header
- **Azure App Service**: `X-MS-CLIENT-PRINCIPAL` header

### User Roles

The application supports two user roles:

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Administrator | Can create, edit, delete todo items |
| `user` | Regular User | Can view todo items and toggle completion status |

By default, all new SSO users are assigned the `user` role.

#### Granting Admin Access

To grant admin access to a user, manually update their role in MongoDB:

```javascript
// In MongoDB shell
db.users.updateOne(
    { email: "your-admin-email@example.com" },
    { $set: { role: "admin" } }
)
```

Or via environment variable (for development):

```env
# Comma-separated list of admin emails
ADMIN_EMAILS=admin@example.com,another-admin@example.com
```

Then update `user_service.py` to check this environment variable.

## Creating a New Feature
- **Databricks**: `X-Databricks-User-Email` header
- **Azure App Service**: `X-MS-CLIENT-PRINCIPAL` header

## Creating a New Feature

1. Create a feature directory under `app/features/`:

```bash
mkdir -p app/features/myfeature
```

2. Add files:

**`app/features/myfeature/__init__.py`** (empty)

**`app/features/myfeature/model.py`**:
```python
from pydantic import Field
from app.models.base import MongoBaseModel

class MyFeatureModel(MongoBaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(default=None, max_length=500)
    completed: bool = False
```

**`app/features/myfeature/schema.py`**:
```python
from pydantic import BaseModel

class MyFeatureCreate(BaseModel):
    name: str
    description: str | None = None

class MyFeatureResponse(BaseModel):
    id: str
    name: str
    description: str | None
    completed: bool
```

**`app/features/myfeature/router.py`**:
```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/myfeature", tags=["myfeature"])

feature_info = {
    "name": "My Feature",
    "url": "/myfeature",
    "description": "Description of my feature",
}

@router.get("/")
async def list_items(request: Request, user: dict = Depends(get_current_user)):
    # Protected route - requires auth
    return {"message": "Hello from my feature!", "user": user}
```

3. Restart the server - your feature will be automatically discovered!

## Authentication Middleware

The `get_current_user` dependency handles authentication:

```python
from fastapi import Depends
from app.auth.middleware import get_current_user

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user": user}
```

For routes that require authentication, you can create a custom dependency:

```python
async def require_user(request: Request) -> dict:
    from app.auth.middleware import get_current_user
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
```

## Database Collections

Use the centralized collection helpers in `app/core/collections.py`:

```python
from app.core.collections import users_collection, todos_collection

# Find users
user = await users_collection.collection.find_one({"email": "test@example.com"})

# Insert document
await todos_collection.collection.insert_one({"title": "My todo"})
```

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: MongoDB with motor (async driver)
- **Authentication**: JWT + OAuth2 + Header-based auth
- **Frontend**: HTMX + Tailwind CSS
- **Templating**: Jinja2

## File Overview

| File | Purpose |
|------|---------|
| `main.py` | App entry point, root route |
| `app/auth/router.py` | OAuth callbacks, auth endpoints |
| `app/auth/middleware.py` | `get_current_user` dependency |
| `app/auth/header_auth.py` | Header-based auth providers |
| `app/auth/user_service.py` | Shared user creation service |
| `app/core/collections.py` | MongoDB collection helpers |
| `app/core/features.py` | Auto-discovery of feature routers |
| `app/templates/landing.html` | Public landing page (no auth required) |
| `app/templates/dashboard/dashboard.html` | Authenticated dashboard |
| `app/templates/todos/todos.html` | Todo list page with sidebar |

