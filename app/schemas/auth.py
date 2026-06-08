from __future__ import annotations

from pydantic import BaseModel, Field


class SendCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32, examples=["+79991234567"])


class SendCodeResponse(BaseModel):
    message: str
    expires_in_seconds: int


class VerifyCodeRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32)
    code: str = Field(pattern=r"^\d{6}$", examples=["123456"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

