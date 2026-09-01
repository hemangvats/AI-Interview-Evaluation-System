from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from auth.schemas import UserRegisterRequest
from auth.security import get_password_hash

# Fallback in-memory storage for users if MongoDB service is offline
LOCAL_USERS: Dict[str, Dict[str, Any]] = {}

class UserRepository:
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db
        self.collection = db["users"] if db is not None else None

    async def get_by_email(self, email: str) -> Optional[dict]:
        email_clean = email.strip().lower()
        if self.collection is not None:
            try:
                user = await self.collection.find_one({"email": email_clean})
                if user:
                    user["_id"] = str(user["_id"])
                    return user
            except Exception as e:
                print(f"MongoDB query error: {e}")

        # Fallback query on local user memory
        for u in LOCAL_USERS.values():
            if u["email"].lower() == email_clean:
                return dict(u)
        return None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        if self.collection is not None:
            try:
                user = await self.collection.find_one({"_id": user_id})
                if user:
                    user["_id"] = str(user["_id"])
                    return user
            except Exception as e:
                print(f"MongoDB query error: {e}")

        # Fallback query on local user memory
        if user_id in LOCAL_USERS:
            return dict(LOCAL_USERS[user_id])
        return None

    async def create(self, request: UserRegisterRequest) -> dict:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        user_document = {
            "_id": user_id,
            "email": request.email.strip().lower(),
            "hashed_password": get_password_hash(request.password),
            "full_name": request.full_name.strip(),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "password_reset_token": None,
            "password_reset_expires": None
        }

        if self.collection is not None:
            try:
                await self.collection.insert_one(dict(user_document))
            except Exception as e:
                print(f"MongoDB insert error: {e}")

        # Always save to local fallback dictionary as well
        LOCAL_USERS[user_id] = user_document
        return user_document
