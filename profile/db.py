import logging
from typing import Optional, Dict, Any
from auth.database import get_database

logger = logging.getLogger(__name__)

# Fallback memory storage if MongoDB is disconnected
_in_memory_profiles: Dict[str, Dict[str, Any]] = {}

class CandidateProfileRepository:
    def __init__(self):
        self.collection_name = "candidate_profiles"

    async def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch candidate profile document by authenticated user_id."""
        db = await get_database()
        if db is not None:
            try:
                doc = await db[self.collection_name].find_one({"user_id": user_id})
                if doc:
                    return doc
            except Exception as e:
                logger.warning(f"Error reading profile from MongoDB for user {user_id}: {e}")

        return _in_memory_profiles.get(user_id)

    async def save_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update candidate profile for authenticated user_id."""
        profile_data["user_id"] = user_id
        db = await get_database()

        if db is not None:
            try:
                # Enforce unique index on user_id
                await db[self.collection_name].create_index("user_id", unique=True)
                await db[self.collection_name].replace_one(
                    {"user_id": user_id},
                    profile_data,
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"Error saving profile to MongoDB for user {user_id}: {e}")

        _in_memory_profiles[user_id] = profile_data
        return profile_data

profile_repo = CandidateProfileRepository()
