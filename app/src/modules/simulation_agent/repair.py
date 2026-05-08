import re
import os
from bs4 import BeautifulSoup
from typing import Optional

from .context_builder import build_enhanced_context_prompt
from .context_builder import retrieve_context


def _fix_unclosed_tags(html: str) -> str:
    # Use BeautifulSoup to repair unclosed/malformed HTML
    soup = BeautifulSoup(html, "html.parser")
    return str(soup)


def _remove_external_resources(html: str) -> str:
    # Remove <script src=> and <link href=> to keep HTML self-contained
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["script", "link", "iframe", "object", "embed"]):
        if tag.name == "script" and tag.get("src"):
            tag.decompose()
        if tag.name == "link" and tag.get("href"):
            tag.decompose()
        if tag.name in ("iframe", "object", "embed"):
            tag.decompose()
    return str(soup)


def _wrap_scripts_with_try_catch(html: str) -> str:
    # Wrap top-level script contents in try/catch to capture runtime errors
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        if not script.get("src") and script.string:
            code = script.string
            # Avoid double-wrapping
            if "__EDUSIM_TRY_WRAPPED__" in code:
                continue
            wrapped = f"try{{\n{code}\n}}catch(e){{window.parent.postMessage({{'type':'sim_error','error':String(e).slice(0,1000),'stack':String(e.stack||'')}} , '*');}}\n//#__EDUSIM_TRY_WRAPPED__"
            script.string.replace_with(wrapped)
    return str(soup)


def _repair_common_js_syntax(html: str) -> str:
    # Heuristic repairs: balance braces and parentheses in inline scripts
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        if not script.get("src") and script.string:
            code = script.string
            # Simple balance check for {}, (), []
            pairs = {"{": "}", "(": ")", "[": "]"}
            stack = []
            for ch in code:
                if ch in pairs:
                    stack.append(pairs[ch])
                elif stack and ch == stack[-1]:
                    stack.pop()
            # If unmatched closers remain, append them
            if stack:
                code = code + "\n" + "\n".join(stack[::-1])
                script.string.replace_with(code)
    return str(soup)


def _restore_missing_controls(html: str, expected_controls: list[dict]) -> str:
    # If controls (sliders/buttons) not present, add a simple control panel div
    soup = BeautifulSoup(html, "html.parser")
    body = soup.body or soup.new_tag("body")
    control_div = soup.new_tag("div", **{"id": "edusim-controls", "style": "position:fixed;right:10px;top:10px;z-index:9999;background:#0b1116;padding:8px;border-radius:8px;"})
    added = False
    for ctrl in expected_controls:
        if ctrl.get("type") == "slider":
            input_tag = soup.new_tag("input")
            input_tag.attrs.update({"type": "range", "min": str(ctrl.get("min", 0)), "max": str(ctrl.get("max", 100)), "value": str(ctrl.get("default", ctrl.get("min",0))), "data-name": ctrl.get("name")})
            control_div.append(input_tag)
            added = True
        elif ctrl.get("type") == "button":
            btn = soup.new_tag("button")
            btn.string = ctrl.get("label","Button")
            btn.attrs.update({"data-name": ctrl.get("name")})
            control_div.append(btn)
            added = True
    if added:
        body.insert(0, control_div)
        if not soup.body:
            soup.html.append(body)
    return str(soup)


def repair_generated_html(html: str, prompt: str, expected_controls: Optional[list[dict]] = None) -> str:
    """Attempt to repair generated HTML using heuristics and BeautifulSoup.

    Steps:
    - Remove external resource tags
    - Fix unclosed/malformed HTML via BeautifulSoup
    - Wrap inline scripts in try/catch to surface runtime errors
    - Make simple JS syntax repairs (balance braces)
    - Restore missing controls if hints provided
    """
    repaired = html
    repaired = _remove_external_resources(repaired)
    repaired = _fix_unclosed_tags(repaired)
    repaired = _wrap_scripts_with_try_catch(repaired)
    repaired = _repair_common_js_syntax(repaired)
    if expected_controls:
        repaired = _restore_missing_controls(repaired, expected_controls)
    return repaired


def quick_sanity_check(html: str) -> bool:
    """Perform quick syntax checks: ensure DOCTYPE and <html> tag present."""
    if "<!DOCTYPE html" not in html.lower():
        return False
    if "<html" not in html.lower() or "<body" not in html.lower():
        return False
    return True
