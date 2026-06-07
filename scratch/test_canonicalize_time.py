import time
import sympy
from services.formula_service import FormulaService

def measure_canonicalize(formula):
    start = time.time()
    print(f"\n--- Canonicalizing: {formula} ---")
    canon, count, derived = FormulaService._canonicalize_formula(formula)
    duration = time.time() - start
    print(f"Canonical: {canon}")
    print(f"Derived: {derived}")
    print(f"Took: {duration:.4f} seconds")

formulas = [
    "F = m*a",
    "P*V = n*R*T",
    "KE = 0.5*m*v^2",
    "x = A*cos(omega*t + phi)"
]

for f in formulas:
    try:
        measure_canonicalize(f)
    except Exception as e:
        print(f"Failed: {e}")
