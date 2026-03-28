from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: int
    email: str
