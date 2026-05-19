from pydantic import BaseModel
from typing import Optional

class RuntimeEventSchema(BaseModel):
    event: str
    object: Optional[str] = None
    velocity: Optional[float] = None
    acceleration: Optional[float] = None
