from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# 创建/更新便签时用的请求体
class NoteCreate(BaseModel):
    type: str  # "clue" 或 "suspect"
    content: str
    pos_x: float = 0
    pos_y: float = 0
    width: float = 200
    height: float = 100
    color: str = "#FFF9C4"
    name: Optional[str] = None

class NoteUpdate(BaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    color: Optional[str] = None
    name:Optional[str] = None

# 返回给前端的便签数据
class NoteOut(BaseModel):
    id: int
    case_id: int
    type: str
    content: str
    pos_x: float
    pos_y: float
    width: float
    height: float
    color: str
    created_at: datetime
    name: Optional[str] = None

    class Config:
        from_attributes = True  # 让 Pydantic 能读取 SQLAlchemy 对象