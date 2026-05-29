import sympy
import string
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

def canonicalize(formula_str):
    parts = formula_str.split("=")
    if len(parts) != 2:
        return None
    lhs, rhs = parts
    try:
        transformations = (standard_transformations + (implicit_multiplication,))
        
        local_dict = {char: sympy.Symbol(char) for char in string.ascii_letters}
        # Also need words like 'delta', 'theta', 'sin', 'cos' etc, but let's just stick to single letters first.
        # It's better to just use standard parse_expr and avoid Q, I issues by specifically mapping them.
        local_dict['Q'] = sympy.Symbol('Q')
        local_dict['I'] = sympy.Symbol('I')
        local_dict['E'] = sympy.Symbol('E')
        local_dict['N'] = sympy.Symbol('N')
        local_dict['O'] = sympy.Symbol('O')
        local_dict['S'] = sympy.Symbol('S')
        
        # We must also support multi-letter words if they appear, so if standard parse_expr encounters them, 
        # local_dict without them will just fall back to standard sympy parsing (which creates symbols for unknown words).
        
        lhs_expr = parse_expr(lhs, transformations=transformations, local_dict=local_dict)
        rhs_expr = parse_expr(rhs, transformations=transformations, local_dict=local_dict)
        
        expr = sympy.simplify(lhs_expr - rhs_expr)
        
        symbols = sorted(list(expr.free_symbols), key=lambda s: s.name)
        if not symbols:
            return None
            
        target = symbols[0]
        solutions = sympy.solve(expr, target)
        if not solutions:
            return str(expr).replace(" ", "")
            
        canon_expr = sympy.Eq(target, solutions[0])
        return str(canon_expr).replace(" ", "")
    except Exception as e:
        print(f"Error parsing {formula_str}: {e}")
        return None

formulas = [
    "F = m*a",
    "a = F/m",
    "m = F/a",
    "P*V = n*R*T",
    "V = n*R*T/P",
    "Q = I*t",
    "I = Q/t",
    "E = m*c**2"
]

for f in formulas:
    print(f"{f} -> {canonicalize(f)}")
