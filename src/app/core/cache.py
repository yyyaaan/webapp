from inspect import iscoroutinefunction
from json import dumps, loads
from logging import getLogger
from os import listdir, makedirs, path, remove

from .config import settings
from .db import transient_data_collection

logger = getLogger("core.cache")

def __file_path_for_key(key: str) -> str:
    file_path = path.join(settings.MEM_DISK_PATH, f"{key}.json")
    makedirs(settings.MEM_DISK_PATH, exist_ok=True)
    return file_path


def __write_to_file(key: str, data: dict):
    file_path = __file_path_for_key(key)
    try:
        with open(file_path, "w") as f:
            f.write(dumps(data))
            logger.info(f"Wrote cache file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to write cache file {file_path}: {e}")
    return None


async def __write_to_transient(key: str, data: dict):
    try:
        await transient_data_collection.update_one(
            {"key": key},
            {"$set": {"value": data}},
            upsert=True,
        )
        logger.info(f"Wrote transient cache for key: {key}")
    except Exception as e:
        logger.error(f"Failed to write transient cache for key {key}: {e}")
    return None


def __cached_from_file(key: str):
    file_path = __file_path_for_key(key)
    try:
        with open(file_path, "r") as f:
            result = loads(f.read())
            logger.info(f"Cache hit from file: {file_path}")
            return result
    except Exception:
        return None


async def __cached_from_transient(key: str):
    """
    Get from transient storage (MongoDB), will attempt to upgrade to local file cache
    """
    record = await transient_data_collection.find_one({"key": key})
    if record:
        logger.info(f"Cache hit from transient storage: {key}. Upgrading to file cache...")
        __write_to_file(key, record["value"])
        return record["value"]
    return None


async def cache_or_run_func(
    func: callable,
    key: str,
    force_update: bool = False,
    to_file: bool = True,
    to_transient: bool = True,
):
    """
    Check cache file & transient storage and run function if needed
    """

    if not force_update:
        result = __cached_from_file(key)
        result = await __cached_from_transient(key) if result is None else result
        if result is not None:
            return result
        logger.info(f"Cache miss for key: {key}. Updating...")
        return await cache_or_run_func(func, key, True, to_file, to_transient)

    result = await func() if iscoroutinefunction(func) else func()

    __write_to_file(key, result)
    await __write_to_transient(key, result)
    return result


async def clear_cache():
    """
    Clear all cache and empty transient storage
    """
    messages = []
    try:
        cached_files = [
            f for f in listdir(settings.MEM_DISK_PATH)
            if f.endswith(".json")
        ]
        logger.info(f"Found cache files to delete: {cached_files}")
        for filename in cached_files:
            file_path = path.join(settings.MEM_DISK_PATH, filename)
            remove(file_path)
        logger.info(f"Deleted cache files: {cached_files}")
        messages.append(f"Deleted {len(cached_files)} cache files.")
    except Exception as e1:
        logger.error(f"Failed to clear cache files: {e1}")
        messages.append(str(e1))

    try:
        delete_result = await transient_data_collection.delete_many({})
        logger.info(f"Cleared transient storage. Deleted {delete_result.deleted_count} items.")
        messages.append(f"Deleted {delete_result.deleted_count} transient items.")
    except Exception as e2:
        logger.error(f"Failed to clear transient storage: {e2}")
        messages.append(str(e2))

    return {"messages": messages}
