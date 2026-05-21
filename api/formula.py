from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from services.formula_service import FormulaService
from models.formula_models import FormulaLabResponse

router = APIRouter()

class ExtractRequest(BaseModel):
    text: str

class LabRequest(BaseModel):
    formula: str

@router.post("/extract")
async def extract_formulas(req: ExtractRequest):
    formulas = FormulaService.extract_formulas(req.text)
    return {"formulas": formulas}

@router.post("/lab", response_model=FormulaLabResponse)
async def get_formula_lab(req: LabRequest):
    res = await FormulaService.get_formula_details(req.formula)
    return res
