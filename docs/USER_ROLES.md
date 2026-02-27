# User Roles and Permissions

This document describes the role-based access control (RBAC) system in the Home Server application.

## Overview

The application implements a simple role-based access control system with two roles:

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Administrator | Full access: create, edit, delete todo items |
| `user` | Regular User | Limited access: view and toggle todo completion |

## Default Behavior

- All new users who sign in via OAuth (GitHub, Google, Microsoft) are assigned the `user` role by default.
- The role is stored in the MongoDB `users` collection and included in the JWT token.

## Granting Admin Access

There are two ways to grant admin access:

### Method 1: Environment Variable (Recommended for Development)

Add email addresses to the `ADMIN_EMAILS` environment variable (comma-separated):

```env
ADMIN_EMAILS=admin@example.com,another-admin@company.com
```

Users whose email matches an entry in this list will automatically be granted admin role on first login.

### Method 2: Direct MongoDB Update

Manually update a user's role in MongoDB:

```javascript
// In MongoDB shell
use home_server

db.users.updateOne(
    { email: "user@example.com" },
    { $set: { role: "admin" } }
)
```

To verify the update:

```javascript
db.users.findOne({ email: "user@example.com" })
```

## Permission Matrix

| Action | admin | user |
|--------|-------|------|
| View todo list | ✓ | ✓ |
| Toggle todo completion | ✓ | ✓ |
| Create new todo | ✓ | ✗ |
| Edit existing todo | ✓ | ✗ |
| Delete todo | ✓ | ✗ |

## Technical Implementation

### User Model

The `User` model includes a `role` field:

```python
from app.models.user import UserRole

class User(MongoBaseModel):
    email: EmailStr
    name: str
    provider: str
    provider_id: str
    avatar_url: str | None = None
    role: UserRole = UserRole.USER  # Default role
    is_active: bool = True
```

### Middleware Dependencies

Two dependencies are available for route protection:

```python
from app.auth.middleware import require_auth, require_admin

# Any authenticated user
@router.get("/todos")
async def list_todos(user: dict = Depends(require_auth)):
    ...

# Admin only
@router.post("/todos/create")
async def create_todo(user: dict = Depends(require_admin)):
    ...
```

### JWT Token

The role is included in the JWT token payload:

```python
{
    "sub": "user_id",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin",  # Included in token
    "exp": 1234567890
}
```

## Frontend UI

### Sidebar

The sidebar displays the user's role next to their email:

- Admin users see: `[#admin]` in green
- Regular users see: `[user]` in gray

### Todo Page

- Admin users see the "NEW TASK" button
- Regular users see a "READ-ONLY MODE" indicator

## Security Considerations

1. **Token-based**: Roles are stored in the JWT token, verified on each request
2. **Server-side enforcement**: All permission checks happen on the server
3. **Database fallback**: ADMIN_EMAILS provides an easy development mechanism, but database role takes precedence for existing users
