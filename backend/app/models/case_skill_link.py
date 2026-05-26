from sqlalchemy import Column, Integer, Boolean, ForeignKey
from app.database import Base

class CaseSkillLink(Base):
    __tablename__ = "case_skill_link"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    enabled = Column(Boolean, default=True)