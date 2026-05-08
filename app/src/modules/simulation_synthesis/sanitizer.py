"""
HTML Sanitization module for EduSim Simulation Synthesis System.
Uses BeautifulSoup to whitelisting-based sanitization combined with regex validation.
Defense-in-depth approach: multiple layers of protection against malicious HTML.
"""

import re
from bs4 import BeautifulSoup, Comment, Doctype
from typing import Set, Dict, List


# Whitelist of safe HTML tags that can be rendered in simulations
SAFE_TAGS = {
    # Structure
    "html", "head", "body", "meta",
    # Sectioning
    "div", "section", "article", "main", "aside", "header", "footer", "nav",
    # Headings
    "h1", "h2", "h3", "h4", "h5", "h6",
    # Text
    "p", "span", "strong", "em", "u", "s", "code", "pre", "blockquote", "small", "mark",
    # Lists
    "ul", "ol", "li", "dl", "dt", "dd",
    # Canvas and SVG
    "canvas", "svg", "g", "path", "circle", "rect", "line", "polygon", "polyline", "ellipse",
    "text", "tspan", "image", "use", "defs", "style", "title",
    # Forms (limited - only read-only inputs)
    "input", "button", "label",
    # Tables
    "table", "tbody", "thead", "tfoot", "tr", "td", "th", "caption", "colgroup", "col",
    # Media (limited)
    "audio", "video", "source",
}

# Whitelist of safe attributes
SAFE_ATTRIBUTES = {
    # Global attributes
    "id", "class", "style", "title", "data-*",
    # HTML5 data attributes (all data-* are allowed)
    # Canvas-specific
    "width", "height",
    # SVG-specific
    "viewBox", "version", "xmlns", "x", "y", "cx", "cy", "r", "x1", "y1", "x2", "y2",
    "fill", "stroke", "stroke-width", "transform", "d", "points", "rx", "ry",
    "text-anchor", "font-size", "font-weight", "font-family", "opacity", "fill-opacity",
    "stroke-linecap", "stroke-linejoin", "stroke-dasharray",
    # Form attributes (limited)
    "type", "min", "max", "step", "value", "disabled", "readonly",
    "name", "placeholder",
    # Input types
    "range", "number", "checkbox", "radio", "button", "submit", "reset", "text",
    # Media attributes
    "src", "controls", "loop", "autoplay", "muted", "preload",
    # Table attributes
    "rowspan", "colspan", "scope",
}

# Patterns to block in attribute values (URLs, scripts, etc.)
BLOCKED_ATTRIBUTE_PATTERNS = [
    r"javascript:",
    r"on\w+\s*=",  # Event handlers: onclick, onload, etc.
    r"data:text/html",  # Data URLs with HTML
    r"vbscript:",
    r"about:",
]

# Inline style properties to block
BLOCKED_STYLE_PROPERTIES = {
    "behavior",  # IE behavior files
    "binding",   # XUL binding
    "-moz-binding",  # Mozilla binding
    "-webkit-binding",  # WebKit binding
}

# Event handler attributes to always strip
EVENT_HANDLERS = {
    "onload", "onerror", "onunload", "onbeforeunload",
    "onclick", "ondblclick", "onmousedown", "onmouseup", "onmouseover", "onmouseout", "onmousemove",
    "onkeydown", "onkeyup", "onkeypress",
    "onfocus", "onblur", "onchange", "onsubmit", "onreset", "onselect",
    "onscroll", "onwheel", "ontouchstart", "ontouchend", "ontouchmove",
    "onanimationstart", "onanimationend", "ontransitionend",
}


def _is_safe_attribute_value(attr_name: str, attr_value: str) -> bool:
    """
    Check if an attribute value is safe.
    Blocks scripts, javascript:, event handlers, and dangerous data URLs.
    """
    if not attr_value or not isinstance(attr_value, str):
        return True

    # Block event handler attributes entirely
    if attr_name.lower() in EVENT_HANDLERS:
        return False

    # Block inline event handlers in any attribute
    for pattern in BLOCKED_ATTRIBUTE_PATTERNS:
        if re.search(pattern, attr_value, re.IGNORECASE):
            return False

    return True


def _sanitize_styles(style_string: str) -> str:
    """
    Parse and sanitize inline CSS styles.
    Removes dangerous CSS properties and blocks external font/image loading.
    """
    if not style_string:
        return ""

    safe_styles = []
    # Split by semicolon and process each declaration
    for declaration in style_string.split(";"):
        if ":" not in declaration:
            continue

        prop, value = declaration.split(":", 1)
        prop = prop.strip().lower()
        value = value.strip()

        # Block dangerous CSS properties
        if any(prop == blocked or prop.startswith(blocked.rstrip("*")) 
               for blocked in BLOCKED_STYLE_PROPERTIES):
            continue

        # Block external font and image loads
        if "url(" in value.lower():
            # Only allow data: URIs and block http://, https://, //
            if any(x in value.lower() for x in ["http://", "https://", "//", "file://"]):
                continue

        # Block @import, @font-face, etc. in style values
        if "@" in value.lower():
            continue

        safe_styles.append(f"{prop}: {value}")

    return "; ".join(safe_styles)


def sanitize_html(html: str) -> str:
    """
    Comprehensive HTML sanitization using BeautifulSoup.
    
    1. Parses HTML structure
    2. Removes/escapes all comments
    3. Whitelists safe tags
    4. Whitelists safe attributes
    5. Sanitizes style values
    6. Blocks dangerous patterns
    7. Reconstructs safe HTML
    
    Returns sanitized HTML safe for rendering in sandboxed iframe.
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        raise ValueError(f"Failed to parse HTML: {e}")

    # Remove all comments (can contain scripts)
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Remove doctype if present (not needed in iframe context)
    for doctype in soup.find_all(string=lambda text: isinstance(text, Doctype)):
        doctype.extract()

    # Recursively sanitize all tags
    def sanitize_tag(tag):
        # Remove unsafe tags
        if tag.name and tag.name.lower() not in SAFE_TAGS:
            # Keep content but remove tag
            tag.unwrap()
            return

        # Sanitize attributes
        if tag.attrs:
            attrs_to_remove = []
            for attr_name in list(tag.attrs.keys()):
                attr_name_lower = attr_name.lower()

                # Remove event handlers
                if attr_name_lower in EVENT_HANDLERS:
                    attrs_to_remove.append(attr_name)
                    continue

                # Check if attribute is whitelisted (or data-* pattern)
                is_safe_attr = (
                    attr_name_lower in SAFE_ATTRIBUTES or
                    attr_name_lower.startswith("data-")
                )
                if not is_safe_attr:
                    attrs_to_remove.append(attr_name)
                    continue

                # Check if attribute value is safe
                attr_value = tag.attrs[attr_name]
                if isinstance(attr_value, list):
                    attr_value = " ".join(attr_value)

                # Sanitize specific attributes
                if attr_name_lower == "style":
                    sanitized_style = _sanitize_styles(attr_value)
                    if sanitized_style:
                        tag.attrs[attr_name] = sanitized_style
                    else:
                        attrs_to_remove.append(attr_name)
                elif not _is_safe_attribute_value(attr_name, attr_value):
                    attrs_to_remove.append(attr_name)

            # Remove unsafe attributes
            for attr_name in attrs_to_remove:
                del tag.attrs[attr_name]

    # Traverse and sanitize all tags
    for tag in soup.find_all(True):  # True = all tags
        sanitize_tag(tag)

    return str(soup)


def validate_html_safety_beautifulsoup(html: str) -> None:
    """
    Additional validation layer after sanitization.
    Checks for remaining dangerous patterns that regex might miss.
    """
    # Check for remaining dangerous patterns
    dangerous_patterns = [
        r"<script",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<form",
        r"on\w+\s*=",  # Event handlers
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            raise ValueError(f"HTML validation failed: Dangerous pattern detected: {pattern}")
