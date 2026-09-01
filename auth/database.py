import logging
from motor.motor_asyncio import AsyncIOMotorClient
from auth.config import auth_settings

logger = logging.getLogger(__name__)

class AuthDatabaseManager:
    client: AsyncIOMotorClient = None
    db = None
    connected: bool = False

auth_db_manager = AuthDatabaseManager()

async def connect_to_mongo() -> None:
    try:
        logger.info("Initializing MongoDB Client for Auth...")
        auth_db_manager.client = AsyncIOMotorClient(
            auth_settings.MONGODB_URL,
            serverSelectionTimeoutMS=2000,
            maxPoolSize=100,
            minPoolSize=10
        )
        # Test connection ping
        await auth_db_manager.client.admin.command('ping')
        auth_db_manager.db = auth_db_manager.client[auth_settings.MONGODB_DB_NAME]
        auth_db_manager.connected = True
        logger.info(f"MongoDB connection established to DB: {auth_settings.MONGODB_DB_NAME}")
    except Exception as e:
        logger.warning(f"MongoDB connection notice: {e}. Auth system active with resilient fallback storage.")
        auth_db_manager.connected = False

async def close_mongo_connection() -> None:
    if auth_db_manager.client:
        auth_db_manager.client.close()
        auth_db_manager.connected = False

async def get_database():
    if auth_db_manager.connected:
        return auth_db_manager.db
    return None
