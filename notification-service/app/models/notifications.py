from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(str, Enum):
    TAX_DEADLINE = "tax_deadline"
    GST_RECONCILIATION = "gst_reconciliation"
    DOCUMENT_PROCESSED = "document_processed"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    WORKFLOW_COMPLETED = "workflow_completed"
    SYSTEM_ALERT = "system_alert"

class NotificationRequest(BaseModel):
    recipient_id: str = Field(..., description="User ID")
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    subject: str = Field(..., max_length=200)
    body: str = Field(..., max_length=2000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    notification_id: str
    status: str
    sent_at: Optional[datetime] = None
    channel_results: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
