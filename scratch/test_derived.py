import asyncio
import json
from services.formula_service import FormulaService

async def test():
    text = r"""
    $$F = ma$$
    $$I = \frac{Q}{t}$$
    $$PV = nRT$$
    """
    
    res = await FormulaService.extract_formulas(text)
    print(json.dumps(res["formulas"], indent=2))

if __name__ == "__main__":
    asyncio.run(test())
