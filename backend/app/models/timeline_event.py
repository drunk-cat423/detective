from sqlalchemy import Column, Integer, String, Text, Float, DateTime as SqlDateTime, ForeignKey, Enum as SqlEnum, func
from app.database import Base
import enum

class EventSource(str, enum.Enum):
    manual = "manual"
    auto = "auto"
    from_note = "from_note"

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    event_time = Column(String(100), nullable=False)
    sort_order = Column(Float, default=0)
    description = Column(Text, nullable=False)
    source = Column(SqlEnum(EventSource), nullable=False)
    related_note_id = Column(Integer, ForeignKey("notes.id"), nullable=True)
    created_at = Column(SqlDateTime, server_default=func.now())