from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.database import Base

class Connection(Base):
    __tablename__ = "connections"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    from_note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    to_note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    label = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())