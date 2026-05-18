from __future__ import annotations

import functools
from typing import Iterable

from tradingagents.agents.utils.fundamental_data_tools import _cached_fundamentals
from tradingagents.dataflows.peer_mapping import resolve_peer_candidates


_PRIORITY_FIELDS = [
    "Name",
    "Sector",
    "Industry",
    "Market Cap",
    "Revenue (TTM)",
    "Gross Profit",
    "EBITDA",
    "Net Income",
    "Profit Margin",
    "Operating Margin",
    "Return on Equity",
    "Debt to Equity",
    "Current Ratio",
    "Free Cash Flow",
    "PE Ratio (TTM)",
    "Forward PE",
    "Price to Book",
    "PEG Ratio",
]


def _parse_fundamentals_block(raw_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in (raw_text or "").splitlines():
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _select_metric_items(parsed: dict[str, str], metric_limit: int) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    for field in _PRIORITY_FIELDS:
        value = parsed.get(field)
        if value:
            selected.append((field, value))
        if len(selected) >= metric_limit:
            break
    return selected


def _format_snapshot(ticker: str, raw_text: str, metric_limit: int) -> str:
    parsed = _parse_fundamentals_block(raw_text)
    if not parsed:
        return f"### {ticker}\nFundamentals unavailable."

    lines = [f"### {ticker}"]
    for field, value in _select_metric_items(parsed, metric_limit):
        lines.append(f"- {field}: {value}")
    return "\n".join(lines)


@functools.lru_cache(maxsize=256)
def _cached_peer_set(ticker: str, curr_date: str, max_peers: int) -> tuple[str, ...]:
    del curr_date  # Reserved for future vendor-backed peer resolution.
    return tuple(resolve_peer_candidates(ticker, max_peers=max_peers))


@functools.lru_cache(maxsize=512)
def _cached_peer_fundamentals(peer_ticker: str, curr_date: str) -> str:
    return _cached_fundamentals(peer_ticker, curr_date)


@functools.lru_cache(maxsize=256)
def _cached_industry_context(ticker: str, curr_date: str) -> str:
    raw = _cached_fundamentals(ticker, curr_date)
    parsed = _parse_fundamentals_block(raw)
    sector = parsed.get("Sector", "Unknown")
    industry = parsed.get("Industry", "Unknown")
    market_cap = parsed.get("Market Cap", "Unknown")
    return (
        f"Sector: {sector}\n"
        f"Industry: {industry}\n"
        f"Target market cap: {market_cap}\n"
        "Cycle context note: Use the peer financial mix and valuation dispersion "
        "to infer whether the thesis is company-specific or mostly industry driven."
    )


def build_industry_inputs(
    ticker: str,
    curr_date: str,
    *,
    max_peers: int,
    metric_limit: int,
) -> dict[str, str | list[str]]:
    target_fundamentals = _cached_fundamentals(ticker, curr_date)
    peers = list(_cached_peer_set(ticker, curr_date, max_peers))
    peer_blocks = [
        _format_snapshot(peer, _cached_peer_fundamentals(peer, curr_date), metric_limit)
        for peer in peers
    ]
    return {
        "target_fundamentals": target_fundamentals,
        "target_snapshot": _format_snapshot(ticker, target_fundamentals, metric_limit),
        "peer_tickers": peers,
        "peer_snapshots": "\n\n".join(peer_blocks) if peer_blocks else "No curated peer set available.",
        "industry_context": _cached_industry_context(ticker, curr_date),
    }
