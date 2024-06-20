from pydantic import BaseModel, Field
from typing import Optional


class BaseLabel(BaseModel):
    label: str
    url: str
    value: Optional[int] = Field(None)


class Label(BaseLabel):
    id: str
