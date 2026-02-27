from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId

from app.core.collections import todos_collection
from app.features.todos.model import TodoItem
from app.auth.middleware import get_current_user, require_admin

router = APIRouter(prefix="/todos", tags=["todos"])
templates = Jinja2Templates(directory="app/templates")

feature_info = {
    "name": "Todo List",
    "url": "/todos",
    "description": "A card-based todo list with customizable layouts",
}


async def require_user(request: Request) -> dict:
    """Dependency that requires authentication"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


@router.get("/", response_class=HTMLResponse)
async def list_todos(request: Request, user: dict = Depends(require_user)):
    """Show the main todos page with all todo cards"""
    from app.core.features import discover_features
    
    features = discover_features()
    todos = await todos_collection.collection.find({}).sort("order", 1).to_list(length=100)

    return templates.TemplateResponse(
        "todos/todos.html",
        {
            "request": request,
            "user": {
                "name": user.get("name", "User"), 
                "email": user.get("email", ""), 
                "avatar_url": None,
                "role": user.get("role", "user"),
            },
            "features": [{"name": f.name, "url": f.url} for f in features],
            "todos": todos,
            "is_admin": user.get("role") == "admin",
        },
    )


@router.post("/create", response_class=HTMLResponse)
async def create_todo(
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    content: str = Form(default=""),
    column_width: int = Form(default=12),
    user: dict = Depends(require_admin),  # Admin only
):
    """Create a new todo card - Admin only"""
    # Clamp column width to 1-12
    column_width = max(1, min(12, column_width))
    
    # Get max order
    last_todo = await todos_collection.collection.find_one(sort=[("order", -1)])
    new_order = (last_todo.get("order", 0) + 1) if last_todo else 0

    todo = TodoItem(
        title=title,
        description=description or None,
        content=content or None,
        column_width=column_width,
        order=new_order,
    )
    
    todo_dict = todo.model_dump(by_alias=True, exclude_none=True)
    todo_dict.pop("_id", None)
    
    result = await todos_collection.collection.insert_one(todo_dict)
    new_todo = await todos_collection.collection.find_one({"_id": result.inserted_id})

    return render_todo_card(new_todo)


@router.post("/{todo_id}/edit", response_class=HTMLResponse)
async def edit_todo(
    request: Request,
    todo_id: str,
    title: str = Form(...),
    description: str = Form(default=""),
    content: str = Form(default=""),
    column_width: int = Form(default=12),
    user: dict = Depends(require_admin),  # Admin only
):
    """Edit an existing todo - Admin only"""
    column_width = max(1, min(12, column_width))
    
    await todos_collection.collection.update_one(
        {"_id": ObjectId(todo_id)},
        {
            "$set": {
                "title": title,
                "description": description or None,
                "content": content or None,
                "column_width": column_width,
                "updated_at": datetime.now(timezone.utc),
            }
        }
    )
    
    updated_todo = await todos_collection.collection.find_one({"_id": ObjectId(todo_id)})
    return render_todo_card(updated_todo)


@router.delete("/{todo_id}", response_class=HTMLResponse)
async def delete_todo(
    request: Request,
    todo_id: str,
    user: dict = Depends(require_admin),  # Admin only
):
    """Delete a todo - Admin only"""
    await todos_collection.collection.delete_one({"_id": ObjectId(todo_id)})
    return HTMLResponse("")


@router.post("/{todo_id}/toggle", response_class=HTMLResponse)
async def toggle_todo(
    request: Request,
    todo_id: str,
    user: dict = Depends(require_user),  # Any authenticated user can toggle
):
    """Toggle todo completion status - Any authenticated user"""
    todo = await todos_collection.collection.find_one({"_id": ObjectId(todo_id)})
    if not todo:
        return HTMLResponse("Todo not found", status_code=404)
    
    new_completed = not todo.get("completed", False)
    
    await todos_collection.collection.update_one(
        {"_id": ObjectId(todo_id)},
        {"$set": {"completed": new_completed, "updated_at": datetime.now(timezone.utc)}}
    )
    
    todo["completed"] = new_completed
    return render_todo_card(todo)


# SVG Icons (defined outside f-string)
REFRESH_ICON = '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>'''

CHECK_ICON = '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'''

EDIT_ICON = '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>'''

DELETE_ICON = '''<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>'''


def render_todo_card(todo: dict) -> HTMLResponse:
    """Render a single todo card HTML"""
    completed = todo.get("completed", False)
    title = todo.get("title", "")
    description = todo.get("description", "")
    content = todo.get("content", "")
    column_width = todo.get("column_width", 12)
    todo_id = str(todo.get("_id", ""))
    
    # Select icon based on completion status
    toggle_icon = REFRESH_ICON if completed else CHECK_ICON
    opacity_class = "opacity-60" if completed else ""
    line_through = "line-through" if completed else ""
    
    html = f'''
    <div class="col-span-{column_width} todo-card" data-id="{todo_id}">
        <div class="cyber-card h-full flex flex-col {opacity_class}">
            <div class="flex justify-between items-start mb-3">
                <h3 class="font-semibold text-lg text-[#e0e0e0] {line_through}">
                    {title}
                </h3>
                <div class="flex gap-1">
                    <button 
                        onclick="editTodo('{todo_id}', '{title}', '{description}', '{content}', {column_width})"
                        class="text-[#6b7280] hover:text-[#00d4ff] p-1 transition-colors">
                        {EDIT_ICON}
                    </button>
                    <button 
                        hx-post="/todos/{todo_id}/toggle"
                        hx-target="closest .todo-card"
                        hx-swap="outerHTML"
                        class="text-[#6b7280] hover:text-[#00ff88] p-1 transition-colors">
                        {toggle_icon}
                    </button>
                    <button 
                        hx-delete="/todos/{todo_id}"
                        hx-target="closest .todo-card"
                        hx-swap="outerHTML"
                        hx-confirm="Are you sure you want to delete this todo?"
                        class="text-[#6b7280] hover:text-[#ff3366] p-1 transition-colors">
                        {DELETE_ICON}
                    </button>
                </div>
            </div>
    '''
    
    if description:
        html += f'<p class="text-[#6b7280] text-sm mb-3">{description}</p>'
    
    if content:
        html += f'''
        <div class="flex-1 bg-[#1c1c2e] p-3 mb-3 border border-[#2a2a3a]">
            <p class="text-[#e0e0e0] text-sm whitespace-pre-wrap">{content}</p>
        </div>
        '''
    
    status_text = "[✓] COMPLETE" if completed else "[ ] PENDING"
    status_class = "text-[#00ff88]" if completed else "text-[#ff00ff]"
    
    html += f'''
            <div class="flex justify-between items-center mt-auto pt-3 border-t border-[#2a2a3a]">
                <span class="text-xs text-[#6b7280] font-mono">COL: {column_width}/12</span>
                <span class="text-xs font-mono {status_class}">{status_text}</span>
            </div>
        </div>
    </div>
    '''
    
    return HTMLResponse(html)
