"""
DOM processing utilities.

Handles minification and extraction of semantically relevant HTML
to reduce token usage when sending DOM context to AI models.
"""

import re
from typing import Optional


# Attributes to preserve during minification
KEEP_ATTRIBUTES = {
    "id", "class", "name", "type", "value", "placeholder", "href", "src",
    "alt", "title", "role", "aria-label", "aria-labelledby", "aria-describedby",
    "data-testid", "data-test", "data-cy", "for", "action", "method",
    "disabled", "checked", "selected", "readonly", "required",
}

# Tags to completely remove (scripts, styles, meta)
REMOVE_TAGS = {"script", "style", "noscript", "svg", "path", "meta", "link"}


def minify_html(html: str, max_length: int = 50000) -> str:
    """
    Minify HTML by stripping non-essential tags and attributes.

    Keeps only semantically meaningful elements and attributes that
    help AI models identify interactive elements and page structure.
    """
    if not html:
        return ""

    result = html

    # Remove tags that add noise
    for tag in REMOVE_TAGS:
        result = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>",
            "",
            result,
            flags=re.DOTALL | re.IGNORECASE,
        )
        result = re.sub(
            rf"<{tag}[^>]*/?>",
            "",
            result,
            flags=re.IGNORECASE,
        )

    # Remove HTML comments
    result = re.sub(r"<!--.*?-->", "", result, flags=re.DOTALL)

    # Strip attributes not in KEEP_ATTRIBUTES
    def _filter_attributes(match: re.Match) -> str:
        tag_name = match.group(1)
        attrs_str = match.group(2)
        closing = match.group(3)

        kept_attrs = []
        for attr_match in re.finditer(
            r'([\w\-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([\w\-]+))', attrs_str
        ):
            attr_name = attr_match.group(1).lower()
            if attr_name in KEEP_ATTRIBUTES or attr_name.startswith("data-test"):
                kept_attrs.append(attr_match.group(0))

        attrs = " " + " ".join(kept_attrs) if kept_attrs else ""
        return f"<{tag_name}{attrs}{closing}>"

    result = re.sub(
        r"<(\w+)((?:\s+[^>]*?)?)(\s*/?)>",
        _filter_attributes,
        result,
    )

    # Collapse whitespace
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r">\s+<", "><", result)
    result = result.strip()

    # Truncate if too long
    if len(result) > max_length:
        result = result[:max_length] + "<!-- truncated -->"

    return result


def extract_interactive_elements(html: str) -> str:
    """
    Extract only interactive elements (inputs, buttons, links, selects)
    from the HTML for focused AI analysis.
    """
    interactive_tags = [
        "input", "button", "a", "select", "textarea",
        "label", "form", "option",
    ]

    elements = []
    for tag in interactive_tags:
        pattern = rf"<{tag}[^>]*(?:>.*?</{tag}>|/>)"
        matches = re.findall(pattern, html, flags=re.DOTALL | re.IGNORECASE)
        elements.extend(matches)

    return "\n".join(elements)


def extract_visible_text(html: str) -> str:
    """Extract visible text content from HTML, stripping all tags."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:10000]
