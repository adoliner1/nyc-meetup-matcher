from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ...database import Base

# Association table for many-to-many relationship between users and groups
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id"), primary_key=True)
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meeting_time = Column(DateTime)
    location = Column(String)
    status = Column(String)  # pending, confirmed, completed, cancelled
    chat_group_id = Column(String, nullable=True)  # For storing SMS group chat ID
    
    # Relationships
    members = relationship("User", secondary=user_groups, back_populates="groups")