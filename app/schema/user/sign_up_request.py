from pydantic import BaseModel


class UserSignUpRequest(BaseModel):
    email: str
    password: str
