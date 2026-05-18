from __future__ import annotations

from typing import Iterable


def truncate_text(text: str, max_chars: int, *, suffix: str = "\n... (truncated) ...") -> str:
    """Trim large prompt blocks to a bounded size."""
    if not text or max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    cutoff = max(0, max_chars - len(suffix))
    return text[:cutoff].rstrip() + suffix


def tail_text(text: str, max_chars: int) -> str:
    """Keep the most recent portion of a transcript-like string."""
    if not text or max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    suffix = text[-max_chars:].lstrip()
    return "... (recent context only) ...\n" + suffix


def build_analyst_brief(
    sections: Iterable[tuple[str, str]],
    *,
    max_chars_per_section: int,
) -> str:
    """Render a compact downstream brief from analyst reports."""
    parts: list[str] = []
    for title, body in sections:
        trimmed = truncate_text(body or "", max_chars_per_section)
        if trimmed:
            parts.append(f"## {title}\n{trimmed}")
    return "\n\n".join(parts)
