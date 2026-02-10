from pydantic import BaseModel


class DevLoginRequest(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: str | None
