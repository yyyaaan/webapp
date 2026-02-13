# Home Server

A modular FastAPI home server with MongoDB backend, OAuth authentication (GitHub, Google, Microsoft), and HTMX + Material Design frontend.

## Features

- **Modular Architecture**: Independent features with separate schemas, models, and routers
- **MongoDB + Motor**: Async MongoDB integration using motor
- **OAuth Authentication**: Support for GitHub, Google, and Microsoft OAuth providers
- **HTMX + Material Design**: Server-rendered UI with interactive components
- **Auto-Discovery**: Features automatically discovered and registered

## Project Structure

```
.
├── app/                    # Main application package
│   ├── auth/              # Authentication module
│   │   ├── providers.py   # OAuth provider registry
│   │   ├── github.py      # GitHub OAuth
│   │   ├── google.py      # Google OAuth
│   │   ├── microsoft.py   # Microsoft OAuth
│   │   └── router.py     # Auth routes
│   ├── core/              # Core application components
│   │   ├── config.py      # App configuration
│   │   ├── database.py    # MongoDB connection
│   │   ├── security.py   # JWT utilities
│   │   └── features.py   # Feature auto-discovery
│   ├── models/            # MongoDB document schemas
│   │   ├── base.py       # Base model with common fields
│   │   ├── user.py       # User model
│   │   └── feature.py   # Feature model
│   ├── schemas/           # Pydantic schemas
│   │   └── base.py      # Base schemas
│   ├── features/          # Modular features
│   │   └── example/     # Example feature (Todo List)
│   │       ├── model.py  # MongoDB model
│   │       ├── schema.py # Pydantic schemas
│   │       └── router.py# Routes (with feature_info)
│   └── templates/         # Jinja2 templates
│       ├── base.html     # Base template with HTMX
│       ├── auth/
│       │   └── login.html # Login page
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
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
FRONTEND_URL=http://localhost:8000
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


## Creating a New Feature

1. Create a feature directory under `app/features/`:

```bash
mkdir -p app/features/myfeature
```

2. Add files:

**`app/features/myfeature/__init__.py`** (empty)

**`app/features/myfeature/model.py`**:
```python
from typing import Optional
from pydantic import Field
from app.models.base import MongoBaseModel

class MyFeatureModel(MongoBaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

    class Settings:
        name = "my_feature_items"
```

**`app/features/myfeature/schema.py`**:
```python
from pydantic import BaseModel

class MyFeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MyFeatureResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
```

**`app/features/myfeature/router.py`**:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/myfeature", tags=["myfeature"])

feature_info = {
    "name": "My Feature",
    "url": "/myfeature",
    "description": "Description of my feature",
}

@router.get("/")
async def list_items():
    return {"message": "Hello from my feature!"}
```

3. Restart the server - your feature will be automatically discovered!

## OAuth Providers

### GitHub
1. Go to https://github.com/settings/developers
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/auth/callback/github`
4. Copy Client ID and Client Secret

### Google
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:8000/auth/callback/google` as authorized redirect URI

### Microsoft
1. Go to https://portal.azure.com/
2. Register a new application
3. Add a platform -> Web
4. Set Redirect URI: `http://localhost:8000/auth/callback/microsoft`
5. Copy Application (client) ID and client secret

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: MongoDB with motor (async driver)
- **Authentication**: JWT + OAuth2
- **Frontend**: HTMX + Material Design (Tailwind CSS)
- **Templating**: Jinja2
