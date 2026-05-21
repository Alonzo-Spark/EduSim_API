from pydantic import BaseModel, Field
from typing import List, Optional

class FormulaVariable(BaseModel):
    symbol: str
    meaning: str
    unit: str = ""

class FormulaControl(BaseModel):
    symbol: str
    label: str
    unit: str = ""
    min: float = 1.0
    max: float = 100.0
    step: float = 1.0
    defaultValue: float = 10.0

class FormulaExample(BaseModel):
    title: str
    content: str

class FormulaBase(BaseModel):
    id: str
    title: str
    formula: str

class FormulaLabResponse(FormulaBase):
    description: str = ""
    variables: List[FormulaControl] = []
    anatomy: List[FormulaVariable] = []
    controls: List[FormulaControl] = []
    examples: List[FormulaExample] = []
    relatedConcepts: List[str] = []
    graphType: str = "auto"
    resultSymbol: str = "y"

class FormulaExtractionResponse(BaseModel):
    formulas: List[dict] # Returning generic dictionaries or FormulaBase
