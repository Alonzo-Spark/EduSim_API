from pydantic import BaseModel
from typing import List

from .formula_schema import FormulaSchema
from .hint_schema import HintSchema

class RuntimePayloadSchema(BaseModel):
    event: str
    topic: str
    overlay_message: str
    formulas: List[FormulaSchema]
    hints: List[HintSchema]
