"""
Yardım istekleri için repository.
"""

from typing import List, Optional
from src.repositories.base_repository import BaseRepository
from src.core.logger import logger


class HelpRepository(BaseRepository):
    """
    Yardım istekleri için veritabanı işlemleri.
    """
    
    def __init__(self, db_client):
        super().__init__(db_client, "help_requests")
    
    def get_open_requests(self, limit: int = 10) -> List[dict]:
        """Açık yardım isteklerini getirir."""
        try:
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                sql = f"SELECT * FROM {self.table_name} WHERE status = 'open' ORDER BY created_at DESC LIMIT ?"
                cursor.execute(sql, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[X] {self.table_name}.get_open_requests hatası: {e}")
            return []
    
    def get_user_requests(self, user_id: str) -> List[dict]:
        """Kullanıcının yardım isteklerini getirir."""
        return self.list(filters={"requester_id": user_id})
    
    def get_user_help_offers(self, user_id: str) -> List[dict]:
        """Kullanıcının yardım ettiği istekleri getirir."""
        return self.list(filters={"helper_id": user_id})
    
    def mark_resolved(self, help_id: str) -> bool:
        """Yardım isteğini çözüldü olarak işaretle."""
        from datetime import datetime
        return self.update(help_id, {
            "status": "resolved",
            "resolved_at": datetime.now().isoformat()
        })
