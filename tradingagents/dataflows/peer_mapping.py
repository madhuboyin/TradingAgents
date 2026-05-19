from __future__ import annotations

from typing import Dict, List


_CURATED_PEER_MAP: Dict[str, List[str]] = {
    "AAPL": ["MSFT", "GOOGL", "SONY", "DELL"],
    "ADBE": ["CRM", "INTU", "MSFT", "ORCL"],
    "AMD": ["NVDA", "INTC", "QCOM", "AVGO"],
    "AMZN": ["WMT", "COST", "SHOP", "BABA"],
    "AVGO": ["NVDA", "AMD", "QCOM", "MRVL"],
    "CRM": ["NOW", "ORCL", "SAP", "ADBE"],
    "COST": ["WMT", "TGT", "KR", "BJ"],
    "GOOG": ["META", "AMZN", "MSFT", "BIDU"],
    "GOOGL": ["META", "AMZN", "MSFT", "BIDU"],
    "INTC": ["AMD", "NVDA", "QCOM", "TXN"],
    "JPM": ["BAC", "C", "GS", "MS"],
    "META": ["GOOGL", "SNAP", "PINS", "RDDT"],
    "MSFT": ["GOOGL", "ORCL", "CRM", "ADBE"],
    "NFLX": ["DIS", "WBD", "ROKU", "PARA"],
    "NOW": ["CRM", "SAP", "ORCL", "ADBE"],
    "NVDA": ["AMD", "AVGO", "INTC", "QCOM"],
    "ORCL": ["MSFT", "SAP", "CRM", "IBM"],
    "PYPL": ["SQ", "FIS", "GPN", "SHOP"],
    "QCOM": ["AVGO", "AMD", "INTC", "MRVL"],
    "SHOP": ["AMZN", "SQ", "PYPL", "WMT"],
    "SNOW": ["MDB", "DDOG", "ESTC", "PLTR"],
    "TSLA": ["GM", "F", "RIVN", "NIO"],
    "UBER": ["LYFT", "DASH", "ABNB", "GRAB"],
    "V": ["MA", "AXP", "PYPL", "COF"],
    "WMT": ["COST", "TGT", "AMZN", "KR"],
}


def resolve_peer_candidates(ticker: str, max_peers: int = 5) -> list[str]:
    """Return a bounded curated peer list for ``ticker``.

    MVP behavior intentionally prefers a deterministic hand-maintained map.
    Unknown tickers return an empty list so the Industry Analyst can degrade
    gracefully without changing existing recommendation quality.
    """
    normalized = (ticker or "").strip().upper()
    peers = _CURATED_PEER_MAP.get(normalized, [])
    return [peer for peer in peers if peer != normalized][: max(0, max_peers)]
