from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .user import User

class GroupBase(BaseModel):
    meeting_time: datetime
    location: str

class GroupCreate(GroupBase):
    member_ids: List[int]

class GroupUpdate(BaseModel):
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None

class Group(GroupBase):
    id: int
    created_at: datetime
    status: str
    chat_group_id: Optional[str] = None
    members: List[User] = []

    class Config:
        from_attributes = True