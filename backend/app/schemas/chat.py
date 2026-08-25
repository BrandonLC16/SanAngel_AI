from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Validated input for the internal development chat endpoint."""

    message: str = Field(min_length=1, max_length=10_000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class ChatResponse(BaseModel):
    """Stable response returned by the internal development chat endpoint."""

    answer: str = Field(min_length=1)
