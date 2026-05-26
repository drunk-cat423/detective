from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConnectionCreate(BaseModel):
    from_note_id: int
    to_note_id: int
    label: Optional[str] = None

class ConnectionUpdate(BaseModel):
    label: Optional[str] = None

class ConnectionOut(BaseModel):
    id: int
    case_id: int
    from_note_id: int
    to_note_id: int
    label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True