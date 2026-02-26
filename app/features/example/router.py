from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.collections import todos_collection
from app.features.example.model import TodoItem
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/todos", tags=["todos"])
templates = Jinja2Templates(directory="app/templates")

feature_info = {
    "name": "Todo List",
    "url": "/todos",
    "description": "A simple todo list example feature",
}


async def require_user(request: Request) -> dict:
    """Dependency that requires authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

@router.get("/", response_class=HTMLResponse)
async def list_todos(request: Request, user: dict | None = Depends(get_current_user)):
    if not user:
        return templates.TemplateResponse("auth/login.html", {"request": request, "providers": ["github", "google", "microsoft"]})

    todos = await todos_collection.collection.find({"completed": False}).to_list(length=100)

    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "user": {"name": user.get("name", "User"), "email": user.get("email", ""), "avatar_url": None},
            "features": [],
        },
    )


@router.post("/create", response_class=HTMLResponse)
async def create_todo(
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    user: dict | None = Depends(get_current_user),
):
    if not user:
        return HTMLResponse("<div>Please login</div>")

    todo = TodoItem(title=title, description=description)
    todo_dict = todo.model_dump(by_alias=True, exclude_none=True)
    todo_dict.pop('_id', None)
    await todos_collection.collection.insert_one(todo_dict)

    todos = await todos_collection.collection.find({"completed": False}).to_list(length=100)

    todo_items_html = ""
    for todo in todos:
        todo_items_html += f"""
        <div class="card material-shadow mb-3 flex items-center justify-between">
            <div>
                <h3 class="font-semibold text-gray-800">{todo['title']}</h3>
                <p class="text-gray-600 text-sm">{todo.get('description', '')}</p>
            </div>
            <button
                hx-post="/todos/{todo['_id']}/complete"
                hx-target="closest .card"
                hx-swap="outerHTML"
                class="btn btn-primary text-sm"
            >
                Complete
            </button>
        </div>
        """

    return HTMLResponse(todo_items_html)


@router.post("/{todo_id}/complete", response_class=HTMLResponse)
async def complete_todo(
    request: Request,
    todo_id: str,
    user: dict | None = Depends(get_current_user),
):
    if not user:
        return HTMLResponse("<div>Please login</div>")

    from bson import ObjectId
    await todos_collection.collection.update_one(
        {"_id": ObjectId(todo_id)},
        {"$set": {"completed": True, "updated_at": datetime.now(timezone.utc)}}
    )

    return HTMLResponse('<div class="card material-shadow mb-3 opacity-50 line-through">Item completed</div>')
