from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Shape of every API error response."""

    detail: str
