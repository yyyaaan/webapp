import os
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@lru_cache()
def get_env_var(key: str, default: str = "") -> str:
    return os.getenv(key, default)
