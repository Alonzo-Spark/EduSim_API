from services.formula_service import FormulaService
import json

formulas = [
    "F = ma",
    "F = 10 \\times 5",
    "F = 50",
    "Q = 0.5 \\times 600",
    "17 = 170",
    "V = IR"
]

for f in formulas:
    canon_sym, symbol_count = FormulaService._canonicalize_formula(f)
    print(f"Formula: {f} -> count: {symbol_count}, canon: {canon_sym}")
