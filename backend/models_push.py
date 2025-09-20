# app/backend/models_push.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class PushSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    endpoint: str
    p256dh: str
    auth: str
    platform: Optional[str] = None     # "web", "ios", "android" (web for PWA)
    added_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)