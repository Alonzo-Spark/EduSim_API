import asyncio
import json
from services.formula_service import FormulaService

async def test():
    text = r"""
    Here are the textbook extractions:
    
    Test Case 1:
    $$F = ma$$
    $$F = 10 \times 5$$
    $$F = 50 \text{ N}$$
    
    Test Case 2:
    $$I = \frac{Q}{t}$$
    $$Q = It$$
    $$t = \frac{Q}{I}$$
    
    Test Case 3:
    $$PV = nRT$$
    $$PV = 2 \times 8.314 \times 300$$
    $$PV = 4988.4$$
    
    Test Case 4:
    $$\sin^2\theta + \cos^2\theta = 1$$
    
    Test Case 5:
    $$v = \frac{s}{t}$$
    $$\text{speed} = \frac{\text{distance}}{\text{time}}$$
    
    Test Case 6:
    $$17 = 170$$
    $$2000 / 1000$$
    $$0.5 \times 600$$
    """
    
    res = await FormulaService.extract_formulas(text)
    print("FORMULAS:")
    print(json.dumps(res["formulas"], indent=2))
    print("\nCALCULATION STEPS:")
    print(json.dumps(res["calculation_steps"], indent=2))

if __name__ == "__main__":
    asyncio.run(test())
