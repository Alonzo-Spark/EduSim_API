from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from services.formula_service import FormulaService
from app.src.models.formula_models import FormulaLabResponse
from app.src.config.database import get_db
from app.src.services.persistence_service import resolve_user_from_authorization, save_formula_explanation_to_chat_history

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
async def get_formula_lab(
    req: LabRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    res = await FormulaService.get_formula_details(req.formula)
    user = resolve_user_from_authorization(authorization, db)
    if user:
        try:
            save_formula_explanation_to_chat_history(db, user, req.formula, res)
            db.commit()
            print("[Database] Chat history saved in the database: updated")
            if hasattr(res, "message"):
                res.message = "Formula history saved successfully."
            elif isinstance(res, dict):
                res["message"] = "Formula history saved successfully."
        except Exception as e:
            db.rollback()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save formula history."})
    return res
