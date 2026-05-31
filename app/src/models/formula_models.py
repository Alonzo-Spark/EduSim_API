from pydantic import BaseModel
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
    canonical_form: str = ""
    primary_formula: str = ""
    derived_forms: List[str] = []
    # Added derived_expressions for dynamic frontend evaluation
    derived_expressions: dict = {}


class FormulaLabResponse(FormulaBase):
    description: str = ""
    purpose: str = ""
    variables: List[FormulaControl] = []
    anatomy: List[FormulaVariable] = []
    controls: List[FormulaControl] = []
    examples: List[FormulaExample] = []
    relatedConcepts: List[str] = []
    applications: List[str] = []
    common_mistakes: List[str] = []
    graphType: str = "auto"
    resultSymbol: str = "y"
    message: Optional[str] = None


class FormulaExtractionResponse(BaseModel):
    formulas: List[dict]
    calculation_steps: List[dict] = []

