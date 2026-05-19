from pydantic import BaseModel

class FormulaSchema(BaseModel):
    name: str
    latex: str
    explanation: str
