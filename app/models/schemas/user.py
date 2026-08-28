from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="FIELD_TECH", pattern="^(ADMIN|FIELD_TECH)$")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: str
