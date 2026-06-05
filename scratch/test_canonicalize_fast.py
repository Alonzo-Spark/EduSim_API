import re
import sympy
import string
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

def strip_latex(s: str) -> str:
    # Handle fraction parsing
    s = re.sub(r"\\frac\s*\{([^}]+)\}\s*\{([^}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sin", "sin", s)
    s = re.sub(r"\\cos", "cos", s)
    s = re.sub(r"\\tan", "tan", s)
    s = re.sub(r"\\theta", "theta", s)
    s = re.sub(r"\\Delta", "Delta", s)
    
    # Handle superscripts
    s = s.replace("^", "**")
    
    s = re.sub(r"\\text\s*\{([^}]*)\}", r"\1", s)
    
    commands = [
        r"\\cdot", r"\\times", r"\\propto", 
        r"\\sqrt", r"\\left", r"\\right"
    ]
    for cmd in commands:
        s = re.sub(cmd, "", s)
        
    s = s.replace("{", "").replace("}", "")
    
    # Implicit multiplication for adjacent single letters so mathjs and sympy can separate them
    # Hide known words first
    words = ['sin', 'cos', 'tan', 'theta', 'Delta', 'speed', 'distance', 'time']
    for i, w in enumerate(words):
        s = s.replace(w, f"__{i}__")
        
    # Insert * between adjacent letters
    while re.search(r"([a-zA-Z])([a-zA-Z])", s):
        s = re.sub(r"([a-zA-Z])([a-zA-Z])", r"\1*\2", s)
        
    # Restore words
    for i, w in enumerate(words):
        s = s.replace(f"__{i}__", w)
        
    return s

def _canonicalize_formula(formula_str: str):
    clean = strip_latex(formula_str)
    parts = clean.split("=")
    if len(parts) != 2:
        return None, 0, {}

    lhs, rhs = parts

    try:
        transformations = (standard_transformations + (implicit_multiplication,))
        local_dict = {char: sympy.Symbol(char) for char in string.ascii_letters}
        local_dict.update({
            'Q': sympy.Symbol('Q'), 'I': sympy.Symbol('I'),
            'E': sympy.Symbol('E'), 'N': sympy.Symbol('N'),
            'O': sympy.Symbol('O'), 'S': sympy.Symbol('S')
        })
        
        # Add support for multi-character variables or variables with underscores/numbers
        # Like F_g, m_1, m_2, r, G, m1, m2
        for word in re.findall(r"[a-zA-Z_0-9]+", clean):
            if word not in local_dict and not word.isdigit():
                local_dict[word] = sympy.Symbol(word)
        
        lhs_expr = parse_expr(lhs, transformations=transformations, local_dict=local_dict)
        rhs_expr = parse_expr(rhs, transformations=transformations, local_dict=local_dict)
        
        expr = sympy.simplify(lhs_expr - rhs_expr)
        
        symbols = sorted(list(expr.free_symbols), key=lambda s: s.name)
        symbol_count = len(symbols)
        if not symbols:
            return None, symbol_count, {}
            
        derived_expressions = {}
        for target in symbols:
            sols = sympy.solve(expr, target)
            if sols:
                derived_expressions[target.name] = str(sols[0]).replace(" ", "").replace("**", "^")

        target = symbols[0]
        solutions = sympy.solve(expr, target)
        if not solutions:
            return str(expr).replace(" ", ""), symbol_count, {}
            
        canon_expr = sympy.Eq(target, solutions[0])
        return str(canon_expr).replace(" ", ""), symbol_count, derived_expressions
    except Exception as e:
        print(f"Error in _canonicalize_formula: {e}")
        words = set(re.findall(r"[a-zA-Z]+", formula_str))
        return None, len(words), {}

if __name__ == "__main__":
    raw_formulas = [
        "F = G \\frac{m_1 m_2}{r^2}",
        "F_g = G \\frac{m_1 m_2}{d^2}",
        "F = G * m1 * m2 / r^2"
    ]
    for rf in raw_formulas:
        print(f"Raw: {rf}")
        canon, count, derived = _canonicalize_formula(rf)
        print(f"  Canonical: {canon}")
        print(f"  Count: {count}")
        print(f"  Derived: {derived}")
