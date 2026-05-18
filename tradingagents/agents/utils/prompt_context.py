from __future__ import annotations

import functools
from typing import Iterable


_HORIZON_ALIASES = {
    "short": "short_term",
    "short_term": "short_term",
    "short-term": "short_term",
    "<1y": "short_term",
    "<1yr": "short_term",
    "<1year": "short_term",
    "medium": "medium_term",
    "medium_term": "medium_term",
    "medium-term": "medium_term",
    "1-2y": "medium_term",
    "1-2yr": "medium_term",
    "1-2years": "medium_term",
    "long": "long_term",
    "long_term": "long_term",
    "long-term": "long_term",
    "3-5y": "long_term",
    "3-5yr": "long_term",
    "3-5years": "long_term",
}


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


def normalize_investment_horizon(horizon: str | None) -> str:
    """Normalize caller-provided horizon strings to a stable internal enum."""
    if not horizon:
        return "short_term"
    key = str(horizon).strip().lower().replace(" ", "_")
    return _HORIZON_ALIASES.get(key, "short_term")


def get_investment_horizon_label(horizon: str | None) -> str:
    normalized = normalize_investment_horizon(horizon)
    labels = {
        "short_term": "Short term (<1 year)",
        "medium_term": "Medium term (1-2 years)",
        "long_term": "Long term (3-5 years)",
    }
    return labels[normalized]


@functools.lru_cache(maxsize=None)
def get_horizon_prompt(horizon: str | None, *, role: str) -> str:
    """Return concise prompt guidance tailored to the investment horizon."""
    normalized = normalize_investment_horizon(horizon)
    base = f"Investment horizon: {get_investment_horizon_label(normalized)}."

    role_guidance = {
        "market": {
            "short_term": "Focus on trend, momentum, volatility, and trade timing over the coming weeks to months.",
            "medium_term": "Focus on multi-quarter trend persistence, regime shifts, and whether current technical conditions support a 1-2 year thesis.",
            "long_term": "Use technicals only as supporting context; emphasize broad regime and long-cycle context rather than short-term entry timing.",
        },
        "sentiment": {
            "short_term": "Treat sentiment, narrative shifts, and near-term catalysts as important inputs.",
            "medium_term": "Use sentiment as a secondary signal; emphasize durable narratives and catalysts that can matter over several quarters.",
            "long_term": "De-emphasize short-lived sentiment swings and focus only on sentiment signals that reveal durable narrative or adoption changes.",
        },
        "news": {
            "short_term": "Prioritize recent headlines, near-term catalysts, earnings setup, and events likely to matter within the next year.",
            "medium_term": "Prioritize developments that can affect earnings power, competitive position, or regulation over the next 1-2 years.",
            "long_term": "Prioritize structural industry, regulatory, and secular developments that can matter over a 3-5 year holding period.",
        },
        "fundamentals": {
            "short_term": "Focus on current financial health, near-term earnings setup, and headline valuation context.",
            "medium_term": "Focus on earnings trajectory, margin durability, capital intensity, and valuation over the next 1-2 years.",
            "long_term": "Focus on balance-sheet resilience, reinvestment capacity, capital allocation, and durability of earnings power over 3-5 years.",
        },
        "research": {
            "short_term": "Weight catalysts, technicals, sentiment, and current macro regime more heavily than distant structural considerations.",
            "medium_term": "Balance current setup with industry dynamics, earnings durability, and valuation over the next 1-2 years.",
            "long_term": "Emphasize structural advantages, industry position, durability, and execution over short-term noise.",
        },
        "risk": {
            "short_term": "Frame risks around event timing, volatility, downside catalysts, and tactical invalidation.",
            "medium_term": "Frame risks around multi-quarter execution, earnings revision risk, macro sensitivity, and valuation compression.",
            "long_term": "Frame risks around moat erosion, capital allocation mistakes, balance-sheet weakness, and structural industry shifts.",
        },
        "trader": {
            "short_term": "Produce an execution-minded recommendation suitable for a holding period of less than one year.",
            "medium_term": "Produce a recommendation suited to a 1-2 year holding period, emphasizing thesis durability over pure timing.",
            "long_term": "Produce a recommendation suited to a 3-5 year holding period, emphasizing durability and long-run compounding potential.",
        },
        "portfolio_manager": {
            "short_term": "Optimize for a sub-1-year decision with clear catalysts, risk controls, and tactical invalidation.",
            "medium_term": "Optimize for a 1-2 year decision with emphasis on earnings path, industry positioning, and valuation discipline.",
            "long_term": "Optimize for a 3-5 year decision with emphasis on durability, industry structure, management quality, and balance-sheet resilience.",
        },
    }

    role_map = role_guidance.get(role, role_guidance["research"])
    return f"{base} {role_map[normalized]}"
