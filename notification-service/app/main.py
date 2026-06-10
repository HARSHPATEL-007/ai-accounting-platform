from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models.notifications import NotificationRequest, NotificationResponse, NotificationChannel
from app.channels.email import EmailChannel
from app.channels.sms import SMSChannel
from app.channels.whatsapp import WhatsAppChannel
from app.core.logging import logger
import uuid

app = FastAPI(title="Notification Service", description="Multi-channel notification delivery", version="1.0.0")

email_channel = EmailChannel()
sms_channel = SMSChannel()
whatsapp_channel = WhatsAppChannel()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}

@app.post("/send", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest, background_tasks: BackgroundTasks):
    """Send notification via specified channels."""
    notification_id = str(uuid.uuid4())
    logger.info("notification_request", notification_id=notification_id, type=request.notification_type, channels=request.channels)

    channel_results = {}

    for channel in request.channels:
        try:
            if channel == NotificationChannel.EMAIL and request.recipient_email:
                result = await email_channel.send(
                    to=request.recipient_email,
                    subject=request.subject,
                    body=request.body
                )
                channel_results["email"] = "sent" if result["success"] else "failed"

            elif channel == NotificationChannel.SMS and request.recipient_phone:
                result = await sms_channel.send(
                    to=request.recipient_phone,
                    body=request.body
                )
                channel_results["sms"] = "sent" if result["success"] else "failed"

            elif channel == NotificationChannel.WHATSAPP and request.recipient_phone:
                result = await whatsapp_channel.send(
                    to=request.recipient_phone,
                    template_name="generic_notification",
                    template_params={"body": request.body}
                )
                channel_results["whatsapp"] = "sent" if result["success"] else "failed"

            elif channel == NotificationChannel.IN_APP:
                # Store in database for in-app notifications
                channel_results["in_app"] = "stored"

            else:
                channel_results[channel.value] = "skipped"

        except Exception as e:
            logger.error("channel_send_failed", channel=channel, error=str(e))
            channel_results[channel.value] = f"error: {str(e)}"

    return NotificationResponse(
        notification_id=notification_id,
        status="completed",
        channel_results=channel_results
    )

@app.post("/batch")
async def send_batch(requests: List[NotificationRequest]):
    """Send batch notifications."""
    results = []
    for req in requests:
        result = await send_notification(req, None)
        results.append(result)
    return {"results": results, "total": len(results)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
