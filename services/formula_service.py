import re
import json
from typing import List, Dict, Any
from app.src.modules.legacy_rag.generator import generate_llm_text_async
from models.formula_models import FormulaLabResponse, FormulaVariable, FormulaControl, FormulaExample

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
    commands = [
        r"\\cdot", r"\\times", r"\\frac", r"\\Delta", r"\\propto", 
        r"\\sin", r"\\cos", r"\\tan", r"\\sqrt", r"\\left", r"\\right"
    ]
    for cmd in commands:
        s = re.sub(cmd, "", s)
    return s.replace("{", "").replace("}", "")

class FormulaService:
    @staticmethod
    def extract_formulas(text: str) -> List[Dict[str, Any]]:
        if not text:
            return []
            
        formulas = []
        seen = set()
        
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
                    
        for idx, formula in enumerate(candidates):
            # deduplicate
            canonical = formula.replace(" ", "").lower()
            
            # STRICT FILTER
            if not re.search(r"[=≈≤≥∝→]", formula):
                continue
                
            if "propto" in canonical or "deltap" in canonical or "andinsiunitstheconstant" in canonical:
                continue
                
            if canonical.isalpha():
                continue
                
            # DEMO FILTER: Force only F=ma for Newton's second law derivations
            if "p=mv" in canonical or "f=km(v-u)/t" in canonical or "v-u/t" in canonical or "f∝" in canonical:
                continue

            if canonical in seen:
                continue
            seen.add(canonical)
            formulas.append({
                "id": f"formula-{idx}",
                "formula": formula,
                "title": "Formula",
                "raw": formula
            })
            
        return formulas

    @staticmethod
    async def get_formula_details(formula: str) -> FormulaLabResponse:
        clean_formula = strip_latex(formula)
        canonical = clean_formula.replace(" ", "").replace("**", "^").replace("·", "").upper()
        
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
                    formula=formula,
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
- variables: array of objects with symbol, label, unit (if applicable), and meaning.
- resultSymbol: string (the symbol being calculated)
Do NOT include markdown block markers, output raw JSON.'''
        
        try:
            llm_text = await generate_llm_text_async(prompt, temperature=0.2, max_output_tokens=500)
            if llm_text:
                # clean up markdown backticks if any
                llm_text = re.sub(r"^```json|```$", "", llm_text.strip(), flags=re.MULTILINE).strip()
                data = json.loads(llm_text)
                controls = []
                anatomy = []
                for v in data.get("variables", []):
                    controls.append(FormulaControl(
                        symbol=v.get("symbol", ""),
                        label=v.get("label", v.get("symbol", "")),
                        unit=v.get("unit", "")
                    ))
                    anatomy.append(FormulaVariable(
                        symbol=v.get("symbol", ""),
                        meaning=v.get("meaning", v.get("label", "")),
                        unit=v.get("unit", "")
                    ))
                return FormulaLabResponse(
                    id="dynamic-formula",
                    title=data.get("title", "Unknown Formula"),
                    formula=formula,
                    description=data.get("description", "A mathematical expression."),
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
            formula=formula,
            description="A scientific or mathematical equation.",
            variables=[],
            controls=[],
            anatomy=[],
            examples=[],
            resultSymbol="y"
        )
