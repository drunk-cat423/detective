from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TimelineEventCreate(BaseModel):
    event_time: str
    description: str
    source: str = "manual"

class TimelineEventUpdate(BaseModel):
    event_time: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[float] = None

class TimelineEventOut(BaseModel):
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