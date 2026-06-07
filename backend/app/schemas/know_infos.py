from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KnownInfoCreate(BaseModel):
    content: str

class KnownInfoUpdate(BaseModel):
    content:str

class KnownInfoOut(BaseModel):
    id:int
    case_id:int
    content: str
    created_at:datetime

    class Config:
        from_attributes:True

