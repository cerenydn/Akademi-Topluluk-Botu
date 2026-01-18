"""
Topluluk yardımlaşma servisi.
"""

from datetime import datetime
from typing import Dict, Any
from src.core.logger import logger
from src.core.exceptions import CemilBotError
from src.commands import ChatManager, ConversationManager
from src.repositories import HelpRepository, UserRepository


class HelpService:
    """
    Topluluk yardımlaşma isteklerini yöneten servis.
    """
    
    def __init__(
        self,
        chat_manager: ChatManager,
        conv_manager: ConversationManager,
        help_repo: HelpRepository,
        user_repo: UserRepository
    ):
        self.chat = chat_manager
        self.conv = conv_manager
        self.repo = help_repo
        self.user_repo = user_repo
    
    async def create_help_request(
        self,
        requester_id: str,
        channel_id: str,
        topic: str,
        description: str
    ) -> str:
        """
        Yardım isteği oluşturur ve kanala block mesajı gönderir.
        
        Returns:
            help_id: Oluşturulan yardım isteğinin ID'si
        """
        try:
            # 1. Veritabanına kaydet
            help_id = self.repo.create({
                "requester_id": requester_id,
                "topic": topic,
                "description": description,
                "channel_id": channel_id,
                "status": "open"
            })
            
            # 2. Kullanıcı bilgisini al
            user_data = self.user_repo.get_by_slack_id(requester_id)
            requester_name = user_data.get('full_name', requester_id) if user_data else requester_id
            
            logger.info(f"[>] Yardım isteği oluşturuldu | Kullanıcı: {requester_name} ({requester_id}) | Konu: {topic}")
            
            # 3. Block mesajı oluştur
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🆘 Yardım İsteği: {topic}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<@{requester_id}>* yardım istiyor:\n\n{description}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "💚 Yardım Et",
                                "emoji": True
                            },
                            "style": "primary",
                            "action_id": "help_offer",
                            "value": help_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📋 Detaylar",
                                "emoji": True
                            },
                            "action_id": "help_details",
                            "value": help_id
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🆔 ID: `{help_id[:8]}...` | 📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                        }
                    ]
                }
            ]
            
            # 4. Mesajı kanala gönder
            response = self.chat.post_message(
                channel=channel_id,
                text=f"🆘 Yardım İsteği: {topic}",
                blocks=blocks
            )
            
            # 5. Message TS'yi kaydet (güncelleme için)
            if response.get("ok"):
                message_ts = response.get("ts")
                self.repo.update(help_id, {"message_ts": message_ts})
                logger.info(f"[+] Yardım isteği mesajı gönderildi | Kanal: {channel_id} | TS: {message_ts}")
            
            return help_id
            
        except Exception as e:
            logger.error(f"[X] HelpService.create_help_request hatası: {e}", exc_info=True)
            raise CemilBotError(f"Yardım isteği oluşturulamadı: {e}")
    
    async def offer_help(self, help_id: str, helper_id: str) -> Dict[str, Any]:
        """
        Birisi 'Yardım Et' butonuna tıkladığında çağrılır.
        
        Returns:
            Dict with success status and message
        """
        try:
            # 1. Yardım isteğini al
            help_request = self.repo.get(help_id)
            if not help_request:
                return {"success": False, "message": "❌ Yardım isteği bulunamadı."}
            
            # 2. Durum kontrolü
            if help_request["status"] != "open":
                status_text = {
                    "in_progress": "Bu yardım isteğine zaten biri yardım ediyor.",
                    "resolved": "Bu yardım isteği çözüldü.",
                    "closed": "Bu yardım isteği kapatıldı."
                }.get(help_request["status"], "Bu yardım isteği artık aktif değil.")
                return {"success": False, "message": f"❌ {status_text}"}
            
            # 3. Kendi isteğine yardım edemez
            if help_request["requester_id"] == helper_id:
                return {"success": False, "message": "❌ Kendi yardım isteğinize yardım edemezsiniz."}
            
            # 4. Yardım isteğini güncelle
            self.repo.update(help_id, {
                "status": "in_progress",
                "helper_id": helper_id
            })
            
            # 5. Kullanıcı bilgilerini al
            requester_data = self.user_repo.get_by_slack_id(help_request["requester_id"])
            helper_data = self.user_repo.get_by_slack_id(helper_id)
            
            requester_name = requester_data.get('full_name', help_request["requester_id"]) if requester_data else help_request["requester_id"]
            helper_name = helper_data.get('full_name', helper_id) if helper_data else helper_id
            
            logger.info(f"[>] Yardım teklifi | Yardım Eden: {helper_name} ({helper_id}) | İsteyen: {requester_name} ({help_request['requester_id']})")
            
            # 6. Yardım eden ve isteyen arasında DM aç
            dm_channel = self.conv.open_conversation(
                users=[help_request["requester_id"], helper_id]
            )
            
            # 7. DM'de hoş geldin mesajı gönder
            dm_blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"👋 *Yardım Bağlantısı Kuruldu!*\n\n"
                            f"<@{helper_id}> yardım etmek istiyor.\n\n"
                            f"*Konu:* {help_request['topic']}\n"
                            f"*Açıklama:* {help_request['description']}\n\n"
                            f"Artık bu kanal üzerinden iletişim kurabilirsiniz! 💬"
                        )
                    }
                }
            ]
            
            self.chat.post_message(
                channel=dm_channel["id"],
                text="Yardım bağlantısı kuruldu!",
                blocks=dm_blocks
            )
            
            # 8. Yardım isteyen kişiye bilgi ver (DM)
            requester_dm = self.conv.open_conversation(users=[help_request["requester_id"]])
            self.chat.post_message(
                channel=requester_dm["id"],
                text=f"✅ <@{helper_id}> yardım etmek istiyor!",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"✅ *Yardım Teklifi Alındı!*\n\n"
                            f"<@{helper_id}> yardım etmek istiyor. "
                            f"DM kanalınız açıldı, oradan devam edebilirsiniz!\n\n"
                            f"*Konu:* {help_request['topic']}"
                        )
                    }
                }]
            )
            
            # 9. Orijinal mesajı güncelle (butonu devre dışı bırak)
            updated_blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"✅ Yardım Ediliyor: {help_request['topic']}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<@{help_request['requester_id']}>* yardım istiyor:\n\n{help_request['description']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *<@{helper_id}>* yardım ediyor"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🆔 ID: `{help_id[:8]}...` | 📅 {datetime.now().strftime('%d.%m.%Y %H:%M')} | ✅ Devam ediyor"
                        }
                    ]
                }
            ]
            
            # Mesajı güncelle
            if help_request.get("message_ts") and help_request.get("channel_id"):
                try:
                    self.chat.client.chat_update(
                        channel=help_request["channel_id"],
                        ts=help_request["message_ts"],
                        text=f"✅ Yardım Ediliyor: {help_request['topic']}",
                        blocks=updated_blocks
                    )
                    logger.info(f"[+] Yardım isteği mesajı güncellendi | Kanal: {help_request['channel_id']}")
                except Exception as e:
                    logger.warning(f"[!] Mesaj güncellenemedi: {e}")
            
            return {
                "success": True,
                "message": f"✅ Yardım bağlantısı kuruldu! <@{help_request['requester_id']}> ile DM kanalınız açıldı.",
                "dm_channel_id": dm_channel["id"]
            }
            
        except Exception as e:
            logger.error(f"[X] HelpService.offer_help hatası: {e}", exc_info=True)
            return {"success": False, "message": "Yardım teklifi verilirken bir hata oluştu."}
    
    def get_help_details(self, help_id: str) -> Dict[str, Any]:
        """Yardım isteği detaylarını getirir."""
        help_request = self.repo.get(help_id)
        if not help_request:
            return None
        
        return help_request
