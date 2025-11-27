from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient
from starlette.responses import HTMLResponse, RedirectResponse, StreamingResponse
import asyncio

from app.auth.security import get_current_user, require_user
from app.core.db import api_key_collection
from app.core.config import settings

router = APIRouter()

templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=HTMLResponse, tags=["Web"])
async def read_root(
    request: Request,
    user: dict | None = Depends(get_current_user)
):
    server_ip = "[Outbound IP Cannot Be Determined]"
    ip_services = ["https://checkip.amazonaws.com", "https://api.ipify.org"]
    async with AsyncClient() as client:
        for url in ip_services:
            try:
                r = await client.get(url, timeout=2.0)
                r.raise_for_status()
                server_ip = r.text.strip()
                break
            except Exception:
                continue

    server_ip += "  " + request.app.state.startup_time.strftime(" | Up since: %Y-%m-%d %H:%M:%S UTC")

    return templates.TemplateResponse(
        "index.html", {"request": request, "user": user, "server_ip": server_ip}
    )


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


@router.get("/chat", response_class=HTMLResponse, tags=["Web"])
async def read_chat(request: Request, user: dict | None = Depends(get_current_user), agent: str = "Default"):
    """Render the chat UI page."""
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "user": user, "agent": agent},
    )


@router.get("/roadmap", response_class=HTMLResponse, tags=["Web"])
async def read_roadmap(request: Request, user: dict | None = Depends(get_current_user)):
    """Render the roadmap page."""
    return templates.TemplateResponse(
        "roadmap.html",
        {"request": request, "user": user},
    )
