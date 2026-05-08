import re
from typing import List, Dict, Any


def _parse_constant_value(constant_str: str) -> float | None:
    # Parse simple patterns like "g = 9.8 m/s^2" or "g=9.8"
    m = re.search(r"=\s*([-+]?[0-9]*\.?[0-9]+)", constant_str)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    return None


def verify_physics_consistency(context: Dict[str, List[str]], html: str) -> Dict[str, Any]:
    """Verify physics-related values and rules. Returns dict with results and issues list."""
    issues = []
    results = {"ok": True, "issues": issues}

    constants = context.get("constants", [])
    formulas = context.get("formulas", [])

    # Check gravity constant
    g_values = []
    for c in constants:
        if re.search(r"\bg\b\s*=", c):
            val = _parse_constant_value(c)
            if val is not None:
                g_values.append(val)
    if g_values:
        # Use average or first
        g = sum(g_values)/len(g_values)
        if not (8.0 <= g <= 10.5):
            issues.append({"type": "gravity_mismatch", "message": f"Detected gravity {g}, expected ~9.8"})
            results["ok"] = False
    else:
        # If no gravity constant found but content mentions gravity, warn
        if re.search(r"gravity|gravitational|g\b", html, flags=re.IGNORECASE):
            issues.append({"type": "missing_gravity", "message": "No gravity constant found in context"})
            results["ok"] = False

    # Formula sanity checks (simple heuristics)
    for f in formulas:
        # Check for common kinematics formulas errors
        if re.search(r"s\s*=\s*u t\b|s\s*=\s*u t|s\s*=\s*u t", f.replace(" ", ""), flags=re.IGNORECASE):
            # crude check — accept
            pass

    # Check html for angle ranges or negative velocities mention
    if re.search(r"angle.*range|launch.*angle", html, flags=re.IGNORECASE):
        # no deep checks here
        pass

    return results
