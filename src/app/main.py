from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, openapi, staticfiles
from logging.config import dictConfig
from os import makedirs
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.logging import LOG_CONFIG
from app.web import route as web_main
from app.web import route_admin as web_admin
from app.auth import router as router_auth
from app.features.chat import router as router_chat
from app.features.energy import router as router_energy
from app.features.system import router as router_system

dictConfig(LOG_CONFIG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_time = datetime.now(timezone.utc)
    makedirs(settings.MEM_DISK_PATH, exist_ok=True)
    yield


app = FastAPI(title="AI Pilot", version="0.0.1", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)
app.mount("/static", staticfiles.StaticFiles(directory="app/static"), name="static")

app.include_router(web_main.router)
app.include_router(web_admin.router)
app.include_router(router_chat.router, tags=["API Chat"])
app.include_router(router_auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(router_system.router, prefix="/api/v3/system", tags=["System"])
app.include_router(router_energy.router, prefix="/api/v3", tags=["API Energy"])


@app.on_event("startup")
def startup_event():
    # from app.core import db2
    # db2.init_connection_pool()
    pass


@app.on_event("shutdown")
def shutdown_event():
    # from app.core import db2
    # db2.close_connection_pool()
    pass



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = openapi.utils.get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {"BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "description": "You may either put API Key or login in frontend and use any non-empty value here."
    }}

    api_router_prefixes = ("/api",)
    all_paths = {}
    for path, path_item in openapi_schema["paths"].items():
        if any(path.startswith(prefix) for prefix in api_router_prefixes):
            for method in path_item:
                path_item[method]["security"] = [{"BearerAuth": []}]
        all_paths[path] = path_item
    openapi_schema["paths"] = all_paths

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
