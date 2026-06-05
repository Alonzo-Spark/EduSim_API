import asyncio
from services.formula_service import FormulaService

async def main():
    # Let's test the dynamic formula details retrieval for Universal Gravitation
    raw_formula = "F = G \\frac{m_1 m_2}{r^2}"
    result = await FormulaService.get_formula_details(raw_formula)
    print("Title:", result.title)
    print("Result Symbol:", result.resultSymbol)
    print("Variables:")
    for v in result.variables:
        print(f"  Symbol: {v.symbol}, Label: {v.label}, Unit: {v.unit}, Min: {v.min}, Max: {v.max}, Step: {v.step}, Default: {v.defaultValue}")
    print("Anatomy:")
    for a in result.anatomy:
        print(f"  Symbol: {a.symbol}, Meaning: {a.meaning}, Unit: {a.unit}")
    print("Derived Expressions:", result.derived_expressions)

if __name__ == "__main__":
    asyncio.run(main())
