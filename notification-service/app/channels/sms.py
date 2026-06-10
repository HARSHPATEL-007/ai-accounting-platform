from typing import Dict, Any
from app.core.logging import logger

class SMSChannel:
    """Send SMS via Twilio or AWS SNS."""

    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def send(self, to: str, body: str) -> Dict[str, Any]:
        logger.info("sending_sms", to=to, message_length=len(body))

        # In production: integrate with Twilio/SNS
        return {
            "success": True,
            "message_id": f"sms_{hash(to + body) % 100000}",
            "provider": "twilio",
            "status": "sent"
        }
