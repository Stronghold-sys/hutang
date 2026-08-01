from typing import Dict, Any, Optional
from app.repositories.base import BaseRepository


class ActivityLogRepository(BaseRepository):
    def __init__(self):
        super().__init__("activity_logs")

    async def log_action(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        try:
            await self.create({
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "old_data": old_data,
                "new_data": new_data,
                "ip_address": ip_address,
                "user_agent": user_agent
            })
        except Exception:
            pass
