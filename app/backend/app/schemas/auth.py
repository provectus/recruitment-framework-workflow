from pydantic import BaseModel, EmailStr


class DevLoginRequest(BaseModel):
    email: EmailStr
    name: str


class StatusResponse(BaseModel):
    status: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: str | None
