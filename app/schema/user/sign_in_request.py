from pydantic import BaseModel


class UserSignInRequest(BaseModel):
    email: str
    password: str
