from pydantic import BaseModel
from typing import List

from .formula_schema import FormulaSchema
from .experiment_schema import ExperimentSchema
from .hint_schema import HintSchema

class EducationalPayload(BaseModel):
    topic: str
    concept_explanation: str
    ai_explanation: str = ""
    formulas: List[FormulaSchema]
    misconceptions: List[str]
    experiments: List[ExperimentSchema]
    observables: List[str]
    hints: List[HintSchema]
    assets: List[str]
    relationships: List[str]
