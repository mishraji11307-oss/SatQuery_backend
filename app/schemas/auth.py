"""
SatQuery AI - Auth & User Schemas
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "geointel@satquery.ai"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "SecurePassword123!"})
    full_name: Optional[str] = Field(None, json_schema_extra={"example": "Dr. Geospatial Analyst"})


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "geointel@satquery.ai"})
    password: str = Field(..., json_schema_extra={"example": "SecurePassword123!"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class AuthMeResponse(BaseModel):
    user: UserResponse
