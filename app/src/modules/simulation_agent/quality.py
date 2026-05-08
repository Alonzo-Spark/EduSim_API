import re
from typing import Dict, Any


def score_simulation(html: str, context: Dict[str, Any], interactions: list) -> Dict[str, Any]:
    """Return a simple quality score (0-100) and breakdown."""
    score = 100
    reasons = []

    # Penalize missing formulas if topic is physics and formulas empty
    if context.get("formulas") is None or len(context.get("formulas", [])) == 0:
        score -= 15
        reasons.append("No formulas extracted from context")

    # Penalize if no interactions
    if not interactions or len(interactions) == 0:
        score -= 20
        reasons.append("No interactive controls detected")

    # Penalize if HTML too large
    if len(html) > 200_000:
        score -= 10
        reasons.append("HTML size > 200KB")

    # Penalize if validation-sensitive patterns present
    blocked = [r"fetch\s*\(|https?:\\/\\/", r"localStorage", r"sessionStorage"]
    for p in blocked:
        if re.search(p, html, flags=re.IGNORECASE):
            score -= 20
            reasons.append(f"Blocked pattern present: {p}")

    # Normalize
    score = max(0, min(100, score))
    return {"score": score, "reasons": reasons}


def optimize_html(html: str) -> str:
    """Basic HTML/CSS/JS minification: remove comments and unnecessary whitespace. Not a full minifier but helps.
    """
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # Collapse multiple whitespace
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"\s{2,}", " ", html)

    # Minify inline JS: remove comments and collapse newlines in <script> blocks
    def _minify_script(m):
        code = m.group(1)
        # remove // comments
        code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)
        # remove /* */ comments
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        code = re.sub(r"\n\s*", "", code)
        return f"<script>{code}</script>"

    html = re.sub(r"<script[^>]*>(.*?)</script>", _minify_script, html, flags=re.DOTALL | re.IGNORECASE)

    # Minify inline styles (very basic)
    html = re.sub(
    r"<style[^>]*>(.*?)</style>",
    lambda m: "<style>" + re.sub(r"\s+", " ", m.group(1)) + "</style>",
    html,
    flags=re.DOTALL | re.IGNORECASE
)

    return html
