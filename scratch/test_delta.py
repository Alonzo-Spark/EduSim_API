import asyncio
from services.formula_service import FormulaService

async def main():
    formula = r"x(t) = A \cos(\omega t + \phi)"
    print("Formula:", formula)
    canon, count, derived = FormulaService._canonicalize_formula(formula)
    print("Canonical:", canon)
    print("Derived:", derived)
    
    details = await FormulaService.get_formula_details(formula)
    print("Variables in Details:")
    for v in details.variables:
        print(f" - {v.symbol}: defaultValue={v.defaultValue}")

if __name__ == "__main__":
    asyncio.run(main())
