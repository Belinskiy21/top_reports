from typing import TypedDict


class JwtPayload(TypedDict):
    sub: str
    email: str
    iat: int
    exp: int
    jti: str
