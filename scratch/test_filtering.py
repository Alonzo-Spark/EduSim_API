import asyncio
import json
from services.formula_service import FormulaService

async def test():
    text = r"""
    We know that Force is given by:
    $$ F = ma $$
    
    If m = 10 and a = 5, we can substitute them:
    $$ F = 10 \times 5 $$
    
    This gives the final force:
    $$ F = 50 $$
    
    Another example is $Q = 0.5 \times 600$.
    Or just $$17 = 170$$.
    """
    
    res = await FormulaService.extract_formulas(text)
    print("FORMULAS:")
    print(json.dumps(res["formulas"], indent=2))
    print("\nCALCULATION STEPS:")
    print(json.dumps(res["calculation_steps"], indent=2))

if __name__ == "__main__":
    asyncio.run(test())
