from typing import Optional, Dict, Any
from src.repositories.base_repository import BaseRepository
from src.clients.database_client import DatabaseClient
from src.core.logger import logger
from src.core.exceptions import DatabaseError

class UserRepository(BaseRepository):
    """
    Kullanıcılar tablosuna özel veri erişim sınıfı.
    """

    def __init__(self, db_client: DatabaseClient):
        super().__init__(db_client, "users")

    def get_by_slack_id(self, slack_id: str) -> Optional[Dict[str, Any]]:
        """Slack ID'ye göre kullanıcı getirir."""
        try:
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                sql = f"SELECT * FROM {self.table_name} WHERE slack_id = ?"
                cursor.execute(sql, (slack_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"[X] UserRepository.get_by_slack_id hatası: {e}")
            raise DatabaseError(str(e))

    def update_by_slack_id(self, slack_id: str, data: Dict[str, Any]) -> bool:
        """Slack ID'ye göre kullanıcıyı günceller."""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [slack_id]

        try:
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                sql = f"UPDATE {self.table_name} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE slack_id = ?"
                cursor.execute(sql, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"[X] UserRepository.update_by_slack_id hatası: {e}")
            raise DatabaseError(str(e))

    def get_users_with_birthday_today(self) -> list:
        """Bugün doğum günü olan kullanıcıları listeler."""
        try:
            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                # SQLite'da ay ve gün kontrolü: strftime('%m-%d', birthday)
                sql = f"SELECT * FROM {self.table_name} WHERE strftime('%m-%d', birthday) = strftime('%m-%d', 'now')"
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[X] UserRepository.get_users_with_birthday_today hatası: {e}")
    def import_from_csv(self, file_path: str) -> int:
        """
        CSV dosyasından kullanıcıları içe aktarır.
        Önce mevcut tabloyu temizler.
        """
        import csv
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                return 0

            with self.db_client.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Tabloyu temizle
                cursor.execute(f"DELETE FROM {self.table_name}")
                
                # 2. Yeni kayıtları ekle
                count = 0
                for row in rows:
                    # CSV kolonları veritabanı ile eşleşmeli
                    # Zorunlu alanlar: slack_id, first_name, surname
                    if 'slack_id' not in row or 'first_name' not in row:
                        continue
                        
                    columns = ', '.join(row.keys())
                    placeholders = ', '.join(['?' for _ in row])
                    values = list(row.values())
                    
                    sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    count += 1
                
                conn.commit()
                logger.info(f"[+] CSV import tamamlandı. {count} kullanıcı eklendi.")
                return count
                
        except Exception as e:
            logger.error(f"[X] UserRepository.import_from_csv hatası: {e}")
            raise DatabaseError(str(e))
