from services.formula_service import FormulaService

def test():
    raw_formulas = [
        "F = G \\frac{m_1 m_2}{r^2}",
        "F_g = G \\frac{m_1 m_2}{d^2}",
        "F = G * m1 * m2 / r^2"
    ]
    for rf in raw_formulas:
        print(f"Raw: {rf}")
        try:
            canon, count, derived = FormulaService._canonicalize_formula(rf)
            print(f"  Canonical: {canon}")
            print(f"  Count: {count}")
            print(f"  Derived: {derived}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test()
