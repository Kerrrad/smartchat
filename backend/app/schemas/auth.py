from pydantic import EmailStr, Field

from app.schemas.common import OrmSchema


class RegisterRequest(OrmSchema):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(OrmSchema):
    login: str = Field(min_length=3, max_length=255, description="Email lub nazwa użytkownika")
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(OrmSchema):
    access_token: str
    token_type: str = "bearer"

