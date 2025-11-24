from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pymongo import ReturnDocument
from secrets import token_hex
from starlette.responses import HTMLResponse

from app.auth.security import require_user, require_admin_user
from app.core.db import api_key_collection
from app.core.config import settings

router = APIRouter()

templates = Jinja2Templates(directory="app/web/templates")


@router.get("/dashboard", response_class=HTMLResponse, tags=["Web"])
async def read_dashboard(request: Request, user: dict = Depends(require_user)):
    api_key_data = await api_key_collection.find_one({"owner_email": user["email"]})
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "api_key_data": api_key_data,
            "settings": settings.get_redacted_dict(),
        }
    )


@router.post("/upsert-api-key", response_class=HTMLResponse, tags=["Web"])
async def upsert_api_key(
    request: Request,
    user: dict = Depends(require_admin_user)
):
    """
    Finds and replaces the user's existing API key or creates a new one.
    This ensures a user can only have one key at a time.
    """
    new_key = f"sk-{token_hex(32)}"
    api_key_data = {
        "key": new_key,
        "owner_email": user["email"],
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }

    await api_key_collection.find_one_and_replace(
        {"owner_email": user["email"]},
        api_key_data,
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return templates.TemplateResponse(
        "_partials/_api_key_display.html",
        {"request": request, "api_key": new_key}
    )


@router.get("/manage-api-key", response_class=HTMLResponse, tags=["Web"])
async def get_manage_api_key_ui(
    request: Request,
    user: dict = Depends(require_admin_user)
):
    api_key_data = await api_key_collection.find_one({"owner_email": user["email"]})
    return templates.TemplateResponse(
        "_partials/_api_key_manager.html",
        {"request": request, "api_key_data": api_key_data}
    )


@router.post("/toggle-api-key-status", response_class=HTMLResponse, tags=["Web"])
async def toggle_api_key_status(
    request: Request,
    user: dict = Depends(require_admin_user)
):
    api_key_data = await api_key_collection.find_one({"owner_email": user["email"]})
    if api_key_data:
        new_status = not api_key_data.get("is_active", False)
        await api_key_collection.update_one(
            {"owner_email": user["email"]},
            {"$set": {"is_active": new_status}}
        )

    fresh_api_key_data = await api_key_collection.find_one({"owner_email": user["email"]})
    return templates.TemplateResponse(
        "_partials/_api_key_manager.html",
        {"request": request, "api_key_data": fresh_api_key_data}
    )
