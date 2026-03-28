from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    id: int
    email: str
    token: str
