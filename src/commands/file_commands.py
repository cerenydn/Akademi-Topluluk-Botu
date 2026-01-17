from typing import List, Optional, Dict, Any
from src.core.logger import logger
from src.core.exceptions import SlackClientError

class FileManager:
    """
    Slack Dosya (Files) işlemlerini merkezi olarak yöneten sınıf.
    Dökümantasyon: https://api.slack.com/methods?filter=files
    """

    def __init__(self, client):
        self.client = client

    def upload_file(self, file_path: str, channels: Optional[str] = None, title: Optional[str] = None, initial_comment: Optional[str] = None) -> Dict[str, Any]:
        """
        Dosya yükler (files.upload_v2 - Modern yöntem).
        """
        try:
            response = self.client.files_upload_v2(
                file=file_path,
                channels=channels,
                title=title,
                initial_comment=initial_comment
            )
            if response["ok"]:
                file_info = response["file"]
                logger.info(f"[+] Dosya yüklendi: {file_info['name']} (ID: {file_info['id']})")
                return file_info
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.upload hatası: {e}")
            raise SlackClientError(str(e))

    def get_info(self, file_id: str) -> Dict[str, Any]:
        """Dosya hakkında bilgi getirir (files.info)."""
        try:
            response = self.client.files_info(file=file_id)
            if response["ok"]:
                return response
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.info hatası: {e}")
            raise SlackClientError(str(e))

    def list_files(self, channel: Optional[str] = None, user: Optional[str] = None, types: str = "all", **kwargs) -> List[Dict[str, Any]]:
        """Dosyaları listeler (files.list)."""
        try:
            response = self.client.files_list(channel=channel, user=user, types=types, **kwargs)
            if response["ok"]:
                files = response.get("files", [])
                logger.info(f"[i] Dosyalar listelendi: {len(files)} adet")
                return files
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.list hatası: {e}")
            raise SlackClientError(str(e))

    def delete_file(self, file_id: str) -> bool:
        """Dosyayı siler (files.delete)."""
        try:
            response = self.client.files_delete(file=file_id)
            if response["ok"]:
                logger.info(f"[-] Dosya silindi: {file_id}")
                return True
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.delete hatası: {e}")
            raise SlackClientError(str(e))

    def delete_comment(self, file_id: str, comment_id: str) -> bool:
        """Dosya yorumunu siler (files.comments.delete)."""
        try:
            response = self.client.files_comments_delete(file=file_id, id=comment_id)
            return response["ok"]
        except Exception as e:
            logger.error(f"[X] files.comments.delete hatası: {e}")
            return False

    def share_public_url(self, file_id: str) -> Dict[str, Any]:
        """Dosyayı dış paylaşıma açar (files.sharedPublicURL)."""
        try:
            response = self.client.files_sharedPublicURL(file=file_id)
            if response["ok"]:
                logger.info(f"[+] Dosya halka açıldı: {file_id}")
                return response["file"]
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.sharedPublicURL hatası: {e}")
            raise SlackClientError(str(e))

    def revoke_public_url(self, file_id: str) -> bool:
        """Dosyanın dış paylaşım iznini kaldırır (files.revokePublicURL)."""
        try:
            response = self.client.files_revokePublicURL(file=file_id)
            if response["ok"]:
                logger.info(f"[-] Dosya paylaşım izni kaldırıldı: {file_id}")
                return True
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.revokePublicURL hatası: {e}")
            raise SlackClientError(str(e))

    # Harici Yükleme (V3/External Upload)
    def get_upload_url_external(self, filename: str, length: int, **kwargs) -> Dict[str, Any]:
        """Harici yükleme için URL alır (files.getUploadURLExternal)."""
        try:
            response = self.client.files_getUploadURLExternal(filename=filename, length=length, **kwargs)
            return response if response["ok"] else {}
        except Exception as e:
            logger.error(f"[X] files.getUploadURLExternal hatası: {e}")
            return {}

    def complete_upload_external(self, files: List[Dict[str, Any]], channel_id: Optional[str] = None, initial_comment: Optional[str] = None) -> bool:
        """Harici yüklemeyi tamamlar (files.completeUploadExternal)."""
        try:
            response = self.client.files_completeUploadExternal(files=files, channel_id=channel_id, initial_comment=initial_comment)
            return response["ok"]
        except Exception as e:
            logger.error(f"[X] files.completeUploadExternal hatası: {e}")
            return False

    # Uzak Dosya (Remote Files) İşlemleri
    def add_remote_file(self, external_id: str, external_url: str, title: str, filetype: str = "auto", **kwargs) -> Dict[str, Any]:
        """Uzak bir servisten dosya ekler (files.remote.add)."""
        try:
            response = self.client.files_remote_add(external_id=external_id, external_url=external_url, title=title, filetype=filetype, **kwargs)
            if response["ok"]:
                logger.info(f"[+] Uzak dosya eklendi: {title}")
                return response["file"]
            raise SlackClientError(response['error'])
        except Exception as e:
            logger.error(f"[X] files.remote.add hatası: {e}")
            raise SlackClientError(str(e))

    def get_remote_info(self, external_id: Optional[str] = None, file_id: Optional[str] = None) -> Dict[str, Any]:
        """Uzak dosya bilgisini getirir (files.remote.info)."""
        try:
            response = self.client.files_remote_info(external_id=external_id, file=file_id)
            return response["file"] if response["ok"] else {}
        except Exception as e:
            logger.error(f"[X] files.remote.info hatası: {e}")
            return {}

    def list_remote_files(self, channel: Optional[str] = None, ts_from: Optional[int] = None, ts_to: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Uzak dosyaları listeler (files.remote.list)."""
        try:
            response = self.client.files_remote_list(channel=channel, ts_from=ts_from, ts_to=ts_to, limit=limit)
            return response.get("files", []) if response["ok"] else []
        except Exception as e:
            logger.error(f"[X] files.remote.list hatası: {e}")
            return []

    def share_remote_file(self, channels: str, external_id: Optional[str] = None, file_id: Optional[str] = None) -> bool:
        """Uzak dosyayı bir kanalda paylaşır (files.remote.share)."""
        try:
            response = self.client.files_remote_share(channels=channels, external_id=external_id, file=file_id)
            return response["ok"]
        except Exception as e:
            logger.error(f"[X] files.remote.share hatası: {e}")
            return False

    def update_remote_file(self, external_id: Optional[str] = None, file_id: Optional[str] = None, **kwargs) -> bool:
        """Uzak dosyayı günceller (files.remote.update)."""
        try:
            response = self.client.files_remote_update(external_id=external_id, file=file_id, **kwargs)
            return response["ok"]
        except Exception as e:
            logger.error(f"[X] files.remote.update hatası: {e}")
            return False

    def remove_remote_file(self, external_id: Optional[str] = None, file_id: Optional[str] = None) -> bool:
        """Uzak dosyayı kaldırır (files.remote.remove)."""
        try:
            response = self.client.files_remote_remove(external_id=external_id, file=file_id)
            return response["ok"]
        except Exception as e:
            logger.error(f"[X] files.remote.remove hatası: {e}")
            return False
