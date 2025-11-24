import motor.motor_asyncio
from .config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_DETAILS)
db = client.fastv3 

api_key_collection = db.get_collection("api_keys")
user_collection = db.get_collection("users")
transient_data_collection = db.get_collection("transient_data")
