from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ReminderCreateRequest(BaseModel):
    message: Optional[str] = Field(None, description="Optional custom reminder message")
    channel: str = Field(default="WHATSAPP", description="Reminder delivery channel")

    model_config = ConfigDict(extra="forbid")


class TenantReminderCreateRequest(BaseModel):
    rent_record_id: UUID = Field(..., description="Target rent record ID for the reminder")
    message: Optional[str] = Field(None, description="Optional custom reminder message")
    channel: str = Field(default="WHATSAPP", description="Reminder delivery channel")

    model_config = ConfigDict(extra="forbid")


class ReminderCreateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    rent_record_id: UUID
    whatsapp_url: str
    message: str
    remaining_amount_paise: int
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReminderListItem(BaseModel):
    id: UUID
    tenant_id: UUID
    rent_record_id: UUID
    channel: str
    message: str
    sent_at: datetime
    created_at: datetime
    whatsapp_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
