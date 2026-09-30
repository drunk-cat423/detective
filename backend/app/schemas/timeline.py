from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TimelineEventCreate(BaseModel):
    title: str = Field(default="", max_length=120)
    event_time: str
    description: str
    source: str = "manual"

class TimelineEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    event_time: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[float] = None

class TimelineEventOut(BaseModel):
    title: str
    id: int
    case_id: int
    event_time: str
    sort_order: float
    description: str
    source: str
    related_note_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
