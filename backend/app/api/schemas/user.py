from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str
    neighborhoods: List[str]
    interests: Optional[List[str]] = []

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    neighborhoods: Optional[List[str]] = None
    interests: Optional[List[str]] = None

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True