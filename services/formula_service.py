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


# A basic registry for generic mapping
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
            if "=" in val:
                candidates.add(val)
                
        for match in re.finditer(inline_regex, text):
            val = match.group(1).strip()
            if "=" in val and re.search(r"[a-zA-Z]", val):
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
            if not re.search(r"[=≈≤≥∝→]", formula):
                continue
                
            canonical = formula.replace(" ", "").lower()
            if "propto" in canonical or "deltap" in canonical or "andinsiunitstheconstant" in canonical:
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
            
            if eq_type == "Formula":
                stats["valid_formulas"] += 1
                # Cache the mappings so get_formula_details knows about derived forms
                FORMULA_GROUP_CACHE[primary] = {
                    "canonical_form": canon,
                    "primary_formula": primary,
                    "derived_forms": derived
                }
                formulas.append(item)
            else:
                calculation_steps.append(item)
                if eq_type == "Substitution Step":
                    stats["substitution_steps"] += 1
                elif eq_type == "Final Answer":
                    stats["final_answers"] += 1
                elif eq_type == "Worked Example":
                    stats["worked_examples"] += 1
                    
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
- purpose: string (What is the primary use of this formula?)
- applications: array of strings (Real world applications)
- common_mistakes: array of strings (Common student mistakes when using this formula)
- variables: array of objects with symbol, label, unit (if applicable), meaning, min (number), max (number), step (number), and defaultValue (number). Provide reasonable bounds for typical educational usage.
- resultSymbol: string (the symbol being calculated)
Do NOT include markdown block markers, output raw JSON.'''
        
        try:
            llm_text = await generate_llm_text_async(prompt, temperature=0.2, max_output_tokens=1000)
            if llm_text:
                # clean up markdown backticks if any
                llm_text = re.sub(r"^```json|```$", "", llm_text.strip(), flags=re.MULTILINE).strip()
                # Repair single backslashes in LaTeX commands that violate JSON escaping rules
                llm_text = re.sub(r'\\(?!n|"|u[0-9a-fA-F]{4})', r'\\\\', llm_text)
                data = json.loads(llm_text)
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
