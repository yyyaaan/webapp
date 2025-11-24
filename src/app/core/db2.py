### NOT YET IN USE ###

from databricks import sql
import asyncio
from typing import List, Dict, Any

from .config import settings

_conn_pool = None

def init_connection_pool():
    global _conn_pool
    if _conn_pool is None:
        _conn_pool = sql.connect(
            server_hostname=settings.DATABRICKS_HOST,
            http_path=settings.DATABRICKS_HTTP_PATH,
            access_token=settings.DATABRICKS_TOKEN,
            # timeout=... optional
        )

def close_connection_pool():
    global _conn_pool
    if _conn_pool:
        _conn_pool.close()
        _conn_pool = None

def _row_to_dict(cursor, row):
    cols = [c[0] for c in cursor.description]
    return dict(zip(cols, row))

def run_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Run a query synchronously and return list of dict rows."""
    if _conn_pool is None:
        init_connection_pool()
    with _conn_pool.cursor() as cursor:
        cursor.execute(query, params)
        try:
            rows = cursor.fetchall()
        except Exception:
            rows = []
        return [_row_to_dict(cursor, r) for r in rows]

async def run_query_async(query: str, params: tuple = ()):
    # Bridge blocking call to threadpool for FastAPI async handlers
    return await asyncio.to_thread(run_query, query, params)

# Example helpers
async def get_api_key(key: str):
    q = f"SELECT * FROM {settings.DATABRICKS_CATALOG}.{settings.DATABRICKS_SCHEMA}.api_keys WHERE key = %s"
    rows = await run_query_async(q, (key,))
    return rows[0] if rows else None

async def create_user(user_id: str, name: str, extra_json: str = None):
    q = f"""
    INSERT INTO {settings.DATABRICKS_CATALOG}.{settings.DATABRICKS_SCHEMA}.users (id, name, metadata)
    VALUES (%s, %s, %s)
    """
    # Note: some connectors require commit behavior; the connector handles it.
    await asyncio.to_thread(run_query, q, (user_id, name, extra_json))