from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import connect_to_mongodb, close_mongodb
from app.auth.router import router as auth_router, init_oauth_providers
from app.core.features import discover_features
from app.core.security import decode_access_token
from app.auth.middleware import get_current_user, get_available_auth_providers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    init_oauth_providers()
    yield
    await close_mongodb()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")

# Serve static files for cyberpunk.css
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Check for authentication
    user = await get_current_user(request)
    
    if user:
        # Authenticated - show dashboard
        features = discover_features()
        return templates.TemplateResponse(
            "dashboard/dashboard.html",
            {
                "request": request,
                "user": {"name": user.get("name", "User"), "email": user.get("email", ""), "avatar_url": None},
                "features": [{"name": f.name, "url": f.url} for f in features],
            },
        )
    
    # Not authenticated - show landing page (no login required)
    providers = get_available_auth_providers(request)
    return templates.TemplateResponse("landing.html", {
        "request": request, 
        "providers": providers,
        "user": None
    })


@app.get("/logout", response_class=HTMLResponse)
async def logout():
    return HTMLResponse("""
    <script>
        document.cookie = "access_token=; path=/; max-age=0";
        window.location.href = "/";
    </script>
    """)


app.include_router(auth_router)

features = discover_features()
for feature in features:
    app.include_router(feature.router)
