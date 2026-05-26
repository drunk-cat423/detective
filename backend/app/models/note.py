from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SqlEnum, func
from app.database import Base
import enum

class NoteType(str, enum.Enum):
    clue = "clue"
    suspect = "suspect"

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    type = Column(SqlEnum(NoteType), nullable=False)
    content = Column(Text, nullable=False)
    pos_x = Column(Float, default=0)
    pos_y = Column(Float, default=0)
    width = Column(Float, default=200)
    height = Column(Float, default=100)
    color = Column(String(20), default="#FFF9C4")
    created_at = Column(DateTime, server_default=func.now())