from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern=r"^(faculty_coordinator|super_admin)$")
    branch: Optional[str] = Field(default=None, max_length=255)


class AdminCreate(AdminBase):
    password_hash: str = Field(..., min_length=1, max_length=255)


class AdminUpdate(BaseModel):
    username: Optional[str] = Field(default=None, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    role: Optional[str] = Field(default=None, pattern=r"^(faculty_coordinator|super_admin)$")
    branch: Optional[str] = Field(default=None, max_length=255)


class AdminResponse(AdminBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
