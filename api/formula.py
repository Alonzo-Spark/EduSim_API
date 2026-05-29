from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.formula_service import FormulaService
from app.src.models.formula_models import FormulaLabResponse

router = APIRouter()

class ExtractRequest(BaseModel):
    text: str

class LabRequest(BaseModel):
    formula: str

@router.post("/extract", response_model=None)
async def extract_formulas(req: ExtractRequest):
    result = await FormulaService.extract_formulas(req.text)
    return result

@router.post("/lab", response_model=FormulaLabResponse)
async def get_formula_lab(req: LabRequest):
    res = await FormulaService.get_formula_details(req.formula)
    return res
