from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings

settings = get_settings()
client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_to_mongodb():
    global client, database
    client = AsyncIOMotorClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]


async def close_mongodb():
    global client
    if client:
        client.close()


def get_database() -> AsyncIOMotorDatabase:
    return database


def get_collection(name: str):
    return database[name]
