import re
import json
import sympy
import string
import difflib
from typing import List, Dict, Any
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication
from app.src.modules.legacy_rag.generator import generate_llm_text_async
from app.src.models.formula_models import FormulaLabResponse, FormulaVariable, FormulaControl, FormulaExample

FORMULA_GROUP_CACHE = {}


FORMULA_REGISTRY = {
    "F=ma": {
        "title": "Newton's Second Law",
        "description": "The rate of change of momentum of a body over time is directly proportional to the force applied, and occurs in the same direction as the applied force.",
        "variables": [
            {"symbol": "F", "label": "Force", "unit": "N", "meaning": "Force applied"},
            {"symbol": "m", "label": "Mass", "unit": "kg", "meaning": "Mass of the object"},
            {"symbol": "a", "label": "Acceleration", "unit": "m/s²", "meaning": "Acceleration"}
        ],
        "resultSymbol": "F"
    },
    "V=IR": {
        "title": "Ohm's Law",
        "description": "The current through a conductor between two points is directly proportional to the voltage across the two points.",
        "variables": [
            {"symbol": "V", "label": "Voltage", "unit": "V", "meaning": "Voltage"},
            {"symbol": "I", "label": "Current", "unit": "A", "meaning": "Current"},
            {"symbol": "R", "label": "Resistance", "unit": "Ω", "meaning": "Resistance"}
        ],
        "resultSymbol": "V"
    },
    "N_1(\\THETA_1)=N_2(\\THETA_2)": {
        "title": "Snell's Law",
        "description": "A formula used to describe the relationship between the angles of incidence and refraction, when referring to light or other waves passing through a boundary between two different isotropic media.",
        "variables": [
            {"symbol": "n_1", "label": "Refractive Index 1", "unit": "", "meaning": "Refractive index of first medium"},
            {"symbol": "\\theta_1", "label": "Angle of Incidence", "unit": "°", "meaning": "Angle of incidence"},
            {"symbol": "n_2", "label": "Refractive Index 2", "unit": "", "meaning": "Refractive index of second medium"},
            {"symbol": "\\theta_2", "label": "Angle of Refraction", "unit": "°", "meaning": "Angle of refraction"}
        ],
        "resultSymbol": "n_2"
    },
}

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


def is_value_substituted(formula: str) -> bool:
    """
    Checks if a formula has specific substituted values, units, or scientific notation
    which indicates it is not a standard general physics/math formula.
    """
    formula_lower = formula.lower()
    
    # 1. Check for decimal numbers that are not standard (we allow 0.5, .5, 0.25, .25)
    decimals = re.findall(r"\d+\.\d+", formula_lower)
    for dec in decimals:
        if dec not in ["0.5", ".5", "0.25", ".25"]:
            return True
            
    # 2. Check for scientific notation or large exponents on 10, e.g., 10^ or 10**
    if "10^" in formula_lower or "10**" in formula_lower or "10\\times" in formula_lower:
        return True
        
    # 3. Check for explicit unit words or text blocks containing units
    unit_words = [
        "year", "years", "month", "months", "day", "days", "hour", "hours", "minute", "minutes", "second", "seconds",
        "meter", "meters", "sec", "sec^", "kg", "kilogram", "kilograms", "gram", "grams", "volt", "volts", "ampere", "amperes",
        "ohm", "ohms", "joule", "joules", "watt", "watts", "newton", "newtons", "kelvin", "celsius", "fahrenheit",
        "au", "astronomical", "unit", "units", "mars", "earth", "sun", "moon", "kg/m", "m/s", "circ", "degree", "degrees"
    ]
    
    text_blocks = re.findall(r"\\text\s*\{([^}]+)\}", formula)
    for block in text_blocks:
        block_clean = block.strip().lower()
        if any(w in block_clean for w in unit_words) or block_clean.isdigit():
            return True
            
    # Check raw formula for standalone unit words
    words = re.findall(r"\b[a-zA-Z]+\b", formula_lower)
    for w in words:
        if w in unit_words:
            return True
            
    # 4. Strip out standard/allowed formula digits/numbers to see if any non-standard numbers remain
    # Remove exponents: e.g. ^2, ^3, ^4, ^-1, ^{2}, ^{-2}, etc.
    s = re.sub(r"\^\{?[-+]?\d+\}?", "", formula)
    s = re.sub(r"\*\*\{?[-+]?\d+\}?", "", s)
    
    # Remove subscripts: e.g. _1, _2, _0, _{1}, _{2}, _{0}, _{t}
    s = re.sub(r"_\{?\d+\}?", "", s)
    
    # Remove standard fractions: e.g. 1/2, 1/3, 1/4, 2/3, 4/3, 3/4, 1/8
    s = re.sub(r"\\frac\s*\{\s*1\s*\}\s*\{\s*[2348]\s*\}", "", s)
    s = re.sub(r"\\frac\s*\{\s*[234]\s*\}\s*\{\s*[34]\s*\}", "", s)
    s = re.sub(r"\b[1234]\s*/\s*[2348]\b", "", s)
    
    # Remove simple coefficient/scaling numbers: 0, 1, 2, 3, 4, 8
    s = re.sub(r"\b[012348]\b", "", s)
    
    # Check if there are any remaining digits (e.g. 90, 180, 360, 50, etc.)
    remaining_digits = re.findall(r"\d+", s)
    if remaining_digits:
        return True
            
    return False


class FormulaService:
    @staticmethod
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
        except Exception:
            # Fallback symbol count using simple regex (unique letters/words)
            words = set(re.findall(r"[a-zA-Z]+", formula_str))
            return None, len(words), {}

    @staticmethod
    async def extract_formulas(text: str) -> Dict[str, Any]:
        if not text:
            return {"formulas": [], "calculation_steps": []}
            
        formulas = []
        
        # Regex to match $$ ... $$ or $ ... $
        display_regex = r"\$\$(.*?)\$\$"
        inline_regex = r"\$([^$\n]+?)\$"
        
        candidates = set()
        
        for match in re.finditer(display_regex, text, re.DOTALL):
            val = match.group(1).strip()
            # Split display blocks by newlines to get individual equations (like the frontend does!)
            for line in val.split("\n"):
                line_cleaned = line.strip()
                if line_cleaned:
                    candidates.add(line_cleaned)
                
        for match in re.finditer(inline_regex, text):
            val = match.group(1).strip()
            candidates.add(val)
                
        if not candidates:
            # Fallback for plain text equations
            for line in text.split("\n"):
                cleaned = line.strip()
                if cleaned and (re.search(r"[=∝→⇒⇌↔≈~]", cleaned) or re.search(r"[A-Z][a-z]?\d*\s*\+", cleaned)):
                    candidates.add(cleaned)
                    
        grouped = {} # maps canonical_form -> { "primary_formula": str, "derived_forms": set }
        
        for formula in candidates:
            # STRICT FILTER
            # Support both raw symbols and LaTeX equivalents like \propto, \approx, \to, \rightarrow, \le, \ge, =
            if not re.search(r"[=≈≤≥∝→]|propto|approx|\\to|\\rightarrow|\\le|\\ge", formula):
                continue
                
            canonical = formula.replace(" ", "").lower()
            if "propto" in canonical or "deltap" in canonical or "andinsiunitstheconstant" in canonical:
                if len(canonical) > 40 and not any(x in canonical for x in ["frac", "sqrt", "sin", "cos"]):
                    continue
                
            if canonical.isalpha():
                continue
                
            canon_sym, symbol_count, derived_expressions = FormulaService._canonicalize_formula(formula)
            group_key = canon_sym if canon_sym else canonical
            
            # Determine equation type and confidence
            confidence = 1.0
            eq_type = "Formula"
            
            clean_for_check = strip_latex(formula)
            parts = clean_for_check.split("=")
            is_final_answer = False
            if len(parts) == 2:
                def is_single_var(s):
                    return bool(re.match(r"^\s*[a-zA-Z_]\s*$", s))
                def is_number(s):
                    return bool(re.match(r"^\s*[\d\.\-]+\s*[a-zA-Z_]*\s*$", s))
                    
                if (is_single_var(parts[0]) and is_number(parts[1])) or (is_single_var(parts[1]) and is_number(parts[0])):
                    is_final_answer = True
            
            if symbol_count == 0:
                eq_type = "Worked Example"
                confidence = 1.0
            elif is_final_answer:
                eq_type = "Final Answer"
                confidence = 0.9
            elif symbol_count == 1:
                eq_type = "Substitution Step"
                confidence = 0.8
            else:
                eq_type = "Formula"
                confidence = 1.0
                
            # Semantic Deduplication for specific physics formulas
            if eq_type == "Formula":
                if "speed" in canonical and "distance" in canonical and "time" in canonical:
                    group_key = "Eq(s,t*v)"
                elif "v" in canonical and "s" in canonical and "t" in canonical:
                    group_key = "Eq(s,t*v)"
                elif "q" in canonical and "i" in canonical and "t" in canonical:
                    group_key = "Eq(I*t,Q)"
                elif canon_sym:
                    group_key = canon_sym

            # String similarity fallback grouping (if canon_sym failed)
            if not canon_sym:
                found_similar = False
                for existing_key in grouped.keys():
                    if difflib.SequenceMatcher(None, group_key, existing_key).ratio() > 0.8:
                        group_key = existing_key
                        found_similar = True
                        break
                        
            if group_key not in grouped:
                grouped[group_key] = {
                    "canonical_form": group_key,
                    "primary_formula": formula,
                    "derived_forms": set(),
                    "equation_type": eq_type,
                    "confidence": confidence
                }
            else:
                if formula != grouped[group_key]["primary_formula"]:
                    grouped[group_key]["derived_forms"].add(formula)
                    
        formulas = []
        calculation_steps = []
        
        # Logging counters
        stats = {
            "total_candidates": len(candidates),
            "valid_formulas": 0,
            "substitution_steps": 0,
            "final_answers": 0,
            "worked_examples": 0,
            "duplicates_merged": 0
        }
        
        for idx, (canon, data) in enumerate(grouped.items()):
            primary = data["primary_formula"]
            derived = list(data["derived_forms"])
            stats["duplicates_merged"] += len(derived)
            
            eq_type = data.get("equation_type", "Formula")
            conf = data.get("confidence", 1.0)
            
            # Recalculate derived expressions for the primary formula to ensure it has them
            _, _, derived_expressions = FormulaService._canonicalize_formula(primary)
            
            item = {
                "id": f"formula-{idx}",
                "formula": primary,
                "title": "Formula",
                "raw": primary,
                "canonical_form": canon,
                "primary_formula": primary,
                "derived_forms": derived,
                "equation_type": eq_type,
                "confidence": conf,
                "derived_expressions": derived_expressions
            }
            
            if eq_type == "Formula" and not is_value_substituted(primary):
                stats["valid_formulas"] += 1
                # Cache the mappings so get_formula_details knows about derived forms
                FORMULA_GROUP_CACHE[primary] = {
                    "canonical_form": canon,
                    "primary_formula": primary,
                    "derived_forms": derived
                }
                formulas.append(item)
            else:
                # Completely discard/remove substituted formulas to save tokens and clean up views
                pass
                    
        print(f"[FormulaService] Extraction Complete. Stats: {json.dumps(stats)}")
            
        return {"formulas": formulas, "calculation_steps": calculation_steps}

    @staticmethod
    async def get_formula_details(formula: str) -> FormulaLabResponse:
        clean_formula = strip_latex(formula)
        canonical = clean_formula.replace(" ", "").replace("**", "^").replace("·", "").upper()
        
        # Fetch cached derived forms if available
        cache_data = FORMULA_GROUP_CACHE.get(formula, {})
        canon_res = FormulaService._canonicalize_formula(formula)
        canon_form_str = canon_res[0] if isinstance(canon_res, tuple) and canon_res[0] is not None else formula
        canon_form = cache_data.get("canonical_form", canon_form_str)
        primary_form = cache_data.get("primary_formula", formula)
        derived_forms = cache_data.get("derived_forms", [])
        
        # Check registry
        for key, def_ in FORMULA_REGISTRY.items():
            key_norm = key.replace(" ", "").upper()
            if key_norm in canonical or canonical in key_norm:
                controls = []
                anatomy = []
                for v in def_["variables"]:
                    controls.append(FormulaControl(
                        symbol=v["symbol"], 
                        label=v["label"], 
                        unit=v["unit"]
                    ))
                    anatomy.append(FormulaVariable(
                        symbol=v["symbol"],
                        meaning=v["meaning"],
                        unit=v["unit"]
                    ))
                
                return FormulaLabResponse(
                    id=key,
                    title=def_["title"],
                    formula=primary_form,
                    canonical_form=canon_form,
                    primary_formula=primary_form,
                    derived_forms=derived_forms,
                    description=def_["description"],
                    variables=controls,
                    controls=controls,
                    anatomy=anatomy,
                    examples=[FormulaExample(title="Example", content="Standard calculation.")],
                    resultSymbol=def_["resultSymbol"]
                )
                
        # LLM Fallback for unknown formula
        prompt = f'''Analyze this scientific or mathematical formula: {clean_formula}
Return a JSON object with:
- title: string (e.g. "Newton's Second Law")
- description: string
- variables: array of objects with symbol, label, unit (if applicable), meaning, min (number), max (number), step (number), and defaultValue (number). Provide reasonable bounds for typical educational usage.
- resultSymbol: string (the symbol being calculated)
Do NOT include markdown block markers, output raw JSON.'''
        
        try:
            llm_text = await generate_llm_text_async(
                prompt,
                temperature=0.2,
                max_output_tokens=1000,
                system_prompt="You are a helpful physics and math assistant that outputs JSON only.",
                response_format={"type": "json_object"}
            )
            if llm_text:
                # clean up markdown backticks if any (json, python, or plain)
                llm_text = llm_text.strip()
                llm_text = re.sub(r"^```(?:json|text|markdown)?|```$", "", llm_text, flags=re.MULTILINE).strip()
                
                try:
                    data = json.loads(llm_text)
                except json.JSONDecodeError:
                    # Repair single backslashes in LaTeX commands that violate JSON escaping rules only if direct parsing fails
                    repaired_text = re.sub(r'\\(?!n|"|u[0-9a-fA-F]{4})', r'\\\\', llm_text)
                    data = json.loads(repaired_text)
                    
                controls = []
                anatomy = []
                for v in data.get("variables", []):
                    controls.append(FormulaControl(
                        symbol=v.get("symbol", ""),
                        label=v.get("label", v.get("symbol", "")),
                        unit=v.get("unit", ""),
                        min=v.get("min", 1.0),
                        max=v.get("max", 100.0),
                        step=v.get("step", 1.0),
                        defaultValue=v.get("defaultValue", 10.0)
                    ))
                    anatomy.append(FormulaVariable(
                        symbol=v.get("symbol", ""),
                        meaning=v.get("meaning", v.get("label", "")),
                        unit=v.get("unit", "")
                    ))
                return FormulaLabResponse(
                    id="dynamic-formula",
                    title=data.get("title", "Unknown Formula"),
                    formula=primary_form,
                    canonical_form=canon_form,
                    primary_formula=primary_form,
                    derived_forms=derived_forms,
                    description=data.get("description", "A mathematical expression."),
                    purpose=data.get("purpose", ""),
                    applications=data.get("applications", []),
                    common_mistakes=data.get("common_mistakes", []),
                    variables=controls,
                    controls=controls,
                    anatomy=anatomy,
                    examples=[FormulaExample(title="Example", content="Dynamically generated.")],
                    resultSymbol=data.get("resultSymbol", "y")
                )
        except Exception as e:
            print(f"LLM formula extraction failed: {e}")
            
        # Absolute fallback
        return FormulaLabResponse(
            id="fallback",
            title="Formula",
            formula=primary_form,
            canonical_form=canon_form,
            primary_formula=primary_form,
            derived_forms=derived_forms,
            description="A scientific or mathematical equation.",
            variables=[],
            controls=[],
            anatomy=[],
            examples=[],
            resultSymbol="y"
        )
