from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator
from pydantic_core import PydanticCustomError

# bcrypt only uses the first 72 bytes of a password (and bcrypt 5 refuses longer input).
MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8

Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class RegisterRequest(BaseModel):
    username: Username = Field(examples=["Puja"])
    email: EmailStr = Field(max_length=255, examples=["puja@example.com"])
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, examples=["StrongPassword123"])

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise PydanticCustomError(
                "password_too_long", f"Password must be at most {MAX_PASSWORD_BYTES} bytes long"
            )
        return value


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["puja@example.com"])
    password: str = Field(min_length=1, examples=["StrongPassword123"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut
