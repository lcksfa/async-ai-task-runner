from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
from app.schemas import TaskStatus


class Task(Base):
    """Task model for storing AI processing tasks"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)  # Make nullable to support flexible model selection
    provider = Column(String(50), nullable=True)  # Add provider field
    priority = Column(Integer, nullable=False, default=1)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Task(id={self.id}, status={self.status}, model={self.model})>"