from pydantic import BaseModel, Field
from typing import Optional


class BaseLecture(BaseModel):
    title: str
    modelUrl: Optional[str] = None


class Lecture(BaseLecture):
    id: str
