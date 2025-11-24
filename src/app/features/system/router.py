from databricks.sdk import WorkspaceClient
from fastapi import APIRouter, Depends
from logging import getLogger

from app.core.config import settings
from app.auth.security import require_admin_user
from app.core.db import user_collection
from app.core.cache import clear_cache

router = APIRouter()
logger = getLogger("feature.system")


@router.get("/settings")
async def get_settings():
    """API endpoint for settings"""
    return settings.get_redacted_dict()


@router.post("/clear-cache", dependencies=[Depends(require_admin_user)])
async def empty_cache():
    return await clear_cache()


@router.post("/databricks/run-job/{job_id}")
async def run_databricks_job(job_id: str, payload: dict = {}):
    """
    API endpoint to run a Databricks job by its ID.\n
    Auth'd by Databricks that forbids anonymous, no additional auth required.\n
    Example: job_id=280864241589080, payload={"param_job_exe_name": "value1", "param_spot_prices": []}
    """
    if len(settings.DATABRICKS_CLIENT_ID) < 5:
        logger.info("Databricks integration is not configured.")
        return {"detail": "Databricks integration is not applicable."}
    
    try:
        job_id_int = int(job_id)
        WorkspaceClient().jobs.run_now(
            job_id=job_id_int,
            notebook_params={
                k: str(v) for k, v in payload.items()
            }
        )
        return {"detail": f"Databricks job {job_id_int} has been triggered."}
    except ValueError:
        return {"detail": "Invalid job ID format. Must be an integer."}
    except Exception as e:
        logger.error(f"Failed to trigger Databricks job {job_id}: {e}")
        return {"detail": f"An error occurred while triggering job {job_id}."}



@router.get("/users", dependencies=[Depends(require_admin_user)])
async def list_users():
    """
    Lists all users (name and role) from the database. Requires admin privileges.
    """
    user_cursor = user_collection.find({}, {"name": 1, "role": 1, "_id": 0})
    users = await user_cursor.to_list(length=None)
    return {"users": users}


@router.get("/users/summary")
async def get_user_summary():
    """
    Provides a summary of user counts (total users and admin users).
    """
    total_users = await user_collection.count_documents({})
    admin_users = await user_collection.count_documents({"role": "admin"})
    logger.info(f"Successful request and connection: Total users: {total_users}, Admin users: {admin_users}")
    return {"total_users": "REDACTED", "admin_users": "REDACTED"}
