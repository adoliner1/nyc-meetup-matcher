from sqlalchemy import Column, Integer, String, ARRAY, Boolean
from sqlalchemy.orm import relationship

from ...database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True)
    hashed_password = Column(String)
    full_name = Column(String)
    neighborhoods = Column(ARRAY(String))
    interests = Column(ARRAY(String))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    groups = relationship("Group", secondary="user_groups", back_populates="members")