from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from app.database import Base

class KnownInfo(Base):
    __tablename__ = "known_infos"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())