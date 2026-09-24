"""Minimal admin authentication wire contracts with redacted password repr."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=1024)


class AdminSessionResponse(BaseModel):
    username: str
    expires_at: datetime
    csrf_token: str
