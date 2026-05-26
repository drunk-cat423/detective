from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, func
from app.database import Base

class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True)     # 存放额外信息，如使用的技能等
    created_at = Column(DateTime, server_default=func.now())