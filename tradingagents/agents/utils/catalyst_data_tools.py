from __future__ import annotations

import functools
import re
from datetime import datetime

import yfinance as yf
from dateutil.relativedelta import relativedelta

from tradingagents.agents.utils.fundamental_data_tools import _cached_fundamentals
from tradingagents.agents.utils.news_data_tools import _cached_news
from tradingagents.dataflows.y_finance import yf_retry


_EVENT_KEYWORDS = [
    ("earnings", "Earnings"),
    ("guidance", "Guidance"),
    ("investor day", "Investor Day"),
    ("conference", "Conference"),
    ("presentation", "Conference"),
    ("fda", "Regulatory"),
    ("approval", "Regulatory"),
    ("trial", "Clinical / Milestone"),
    ("launch", "Product Launch"),
    ("rollout", "Product Launch"),
    ("partnership", "Partnership"),
    ("contract", "Commercial"),
    ("order", "Commercial"),
    ("acquisition", "Corporate"),
    ("merger", "Corporate"),
]


def _parse_fundamentals_block(raw_text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in (raw_text or "").splitlines():
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _format_if_present(label: str, value) -> str | None:
    if value is None or value == "":
        return None
    return f"- {label}: {value}"


def _safe_datetime_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime().strftime("%Y-%m-%d")
        except Exception:
            return None
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            return None
    text = str(value).strip()
    return text or None


@functools.lru_cache(maxsize=256)
def _cached_earnings_calendar(ticker: str, curr_date: str) -> str:
    del curr_date  # Future enhancement: strictly filter by trade date source.
    try:
        ticker_obj = yf.Ticker(ticker.upper())
        calendar = yf_retry(lambda: ticker_obj.calendar)

        lines = [f"### {ticker.upper()} Earnings Calendar"]

        if calendar is None:
            return "\n".join(lines + ["- No calendar data available."])

        if hasattr(calendar, "index") and hasattr(calendar, "columns"):
            for idx in list(calendar.index)[:8]:
                raw_value = calendar.loc[idx].iloc[0] if len(calendar.loc[idx].shape) > 0 else calendar.loc[idx]
                value = _safe_datetime_string(raw_value) or str(raw_value)
                lines.append(f"- {idx}: {value}")
            return "\n".join(lines)

        if isinstance(calendar, dict):
            for key, value in list(calendar.items())[:8]:
                if isinstance(value, (list, tuple)):
                    rendered = ", ".join(filter(None, (_safe_datetime_string(item) or str(item) for item in value)))
                else:
                    rendered = _safe_datetime_string(value) or str(value)
                lines.append(f"- {key}: {rendered}")
            return "\n".join(lines)

        return "\n".join(lines + [f"- Raw calendar: {calendar}"])
    except Exception as exc:
        return f"### {ticker.upper()} Earnings Calendar\n- Unavailable: {type(exc).__name__}: {exc}"


@functools.lru_cache(maxsize=256)
def _cached_expectation_context(ticker: str, curr_date: str) -> str:
    fundamentals = _parse_fundamentals_block(_cached_fundamentals(ticker, curr_date))

    try:
        ticker_obj = yf.Ticker(ticker.upper())
        info = yf_retry(lambda: ticker_obj.info) or {}
    except Exception:
        info = {}

    lines = [f"### {ticker.upper()} Expectation Context"]

    for item in (
        _format_if_present("Revenue Growth", info.get("revenueGrowth")),
        _format_if_present("Earnings Growth", info.get("earningsGrowth")),
        _format_if_present("Earnings Quarterly Growth", info.get("earningsQuarterlyGrowth")),
        _format_if_present("Forward EPS", info.get("forwardEps") or fundamentals.get("Forward EPS")),
        _format_if_present("Trailing EPS", info.get("trailingEps") or fundamentals.get("EPS (TTM)")),
        _format_if_present("Forward PE", info.get("forwardPE") or fundamentals.get("Forward PE")),
        _format_if_present("Trailing PE", info.get("trailingPE") or fundamentals.get("PE Ratio (TTM)")),
        _format_if_present("Target Mean Price", info.get("targetMeanPrice")),
        _format_if_present("Recommendation Mean", info.get("recommendationMean")),
        _format_if_present("Current Price", info.get("currentPrice")),
    ):
        if item:
            lines.append(item)

    if len(lines) == 1:
        lines.append("- Expectation context is sparse; use the catalyst map with lower confidence.")

    return "\n".join(lines)


def _classify_event(title: str) -> str:
    lowered = title.lower()
    for keyword, label in _EVENT_KEYWORDS:
        if keyword in lowered:
            return label
    return "General Catalyst"


def _extract_headlines(news_block: str) -> list[str]:
    headlines: list[str] = []
    for line in (news_block or "").splitlines():
        if not line.startswith("### "):
            continue
        title = re.sub(r"\s+\(source:.*\)$", "", line[4:]).strip()
        if title:
            headlines.append(title)
    return headlines


@functools.lru_cache(maxsize=256)
def _cached_event_calendar(ticker: str, curr_date: str, lookahead_days: int, max_events: int) -> str:
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    lookback_days = min(max(30, lookahead_days // 2), 120)
    start_dt = end_dt - relativedelta(days=lookback_days)
    news_block = _cached_news(
        ticker,
        start_dt.strftime("%Y-%m-%d"),
        end_dt.strftime("%Y-%m-%d"),
    )

    headlines = _extract_headlines(news_block)
    lines = [f"### {ticker.upper()} Event Inventory", f"- Lookahead window: {lookahead_days} days", "- Source note: Derived from recent targeted company news; future timing may be uncertain unless explicitly scheduled."]

    seen_titles = set()
    for title in headlines:
        normalized = title.lower()
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        lines.append(f"- [{_classify_event(title)}] {title}")
        if len(seen_titles) >= max_events:
            break

    if len(seen_titles) == 0:
        lines.append("- Event calendar is sparse in the available data.")

    return "\n".join(lines)


def build_catalyst_inputs(
    ticker: str,
    curr_date: str,
    *,
    lookahead_days: int,
    max_events: int,
) -> dict[str, str | int]:
    return {
        "earnings_calendar": _cached_earnings_calendar(ticker, curr_date),
        "expectation_context": _cached_expectation_context(ticker, curr_date),
        "event_calendar": _cached_event_calendar(ticker, curr_date, lookahead_days, max_events),
        "lookahead_days": lookahead_days,
        "max_events": max_events,
    }
