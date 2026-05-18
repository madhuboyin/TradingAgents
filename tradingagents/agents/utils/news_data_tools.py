from langchain_core.tools import tool
from typing import Annotated, Optional
import functools
from tradingagents.dataflows.interface import route_to_vendor


@functools.lru_cache(maxsize=256)
def _cached_news(ticker: str, start_date: str, end_date: str) -> str:
    return route_to_vendor("get_news", ticker, start_date, end_date)


@functools.lru_cache(maxsize=256)
def _cached_global_news(curr_date: str, look_back_days: Optional[int], limit: Optional[int]) -> str:
    return route_to_vendor("get_global_news", curr_date, look_back_days, limit)


@functools.lru_cache(maxsize=256)
def _cached_insider_transactions(ticker: str) -> str:
    return route_to_vendor("get_insider_transactions", ticker)

@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve news data for a given ticker symbol.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing news data
    """
    return _cached_news(ticker, start_date, end_date)

@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[Optional[int], "Days to look back; omit to use the configured default"] = None,
    limit: Annotated[Optional[int], "Max articles to return; omit to use the configured default"] = None,
) -> str:
    """
    Retrieve global news data.
    Uses the configured news_data vendor. Defaults for look_back_days and
    limit come from DEFAULT_CONFIG (global_news_lookback_days,
    global_news_article_limit); pass explicit values to override.

    Args:
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back; omit to inherit config
        limit (int): Maximum number of articles to return; omit to inherit config

    Returns:
        str: A formatted string containing global news data
    """
    return _cached_global_news(curr_date, look_back_days, limit)

@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
    Returns:
        str: A report of insider transaction data
    """
    return _cached_insider_transactions(ticker)
