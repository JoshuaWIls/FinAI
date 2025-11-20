# /app/services/yfinance_service.py
import yfinance as yf
import pandas as pd
import asyncio
from fastapi import HTTPException
from typing import Dict, Any, List

# ===============================
#        HISTORICAL DATA
# ===============================

def fetch_stock_data_sync(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Sync historical data using yfinance with robust validation.
    Uses yf.Ticker(...).history which is the most reliable.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)
        if df is None or df.empty:
            raise ValueError(f"No historical data returned for {ticker}")
        return df
    except Exception as e:
        print(f"[ERROR] fetch_stock_data_sync({ticker}): {e}")
        raise HTTPException(status_code=404, detail=f"Failed to fetch historical data for {ticker}")

async def fetch_stock_data_async(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Async wrapper for historical data."""
    return await asyncio.to_thread(fetch_stock_data_sync, ticker, period, interval)


# ===============================
#         STOCK INFO (SAFE)
# ===============================

def get_ticker_info_sync(ticker: str) -> Dict[str, Any]:
    """
    Get ticker metadata in a safe way. Prefer fast_info and fallbacks.
    Returns a dict with keys we care about (last_price, beta, shortName, marketCap, etc.)
    """
    try:
        t = yf.Ticker(ticker)

        # fast_info is more robust when available
        fast = getattr(t, "fast_info", None) or {}
        info: Dict[str, Any] = {}

        # price
        price = (
            fast.get("last_price")
            or fast.get("regularMarketPrice")
            or getattr(t, "info", {}).get("regularMarketPrice")
        )

        # beta
        beta = fast.get("beta") or getattr(t, "info", {}).get("beta")

        # name
        short_name = getattr(t, "info", {}).get("shortName") or getattr(t, "info", {}).get("longName")

        # collect into info dict
        info["last_price"] = price
        info["beta"] = beta
        info["shortName"] = short_name
        info["raw_info"] = getattr(t, "info", {})  # keep raw info if caller needs more fields

        # if there is absolutely no price we will still return the dict and let caller decide
        return info

    except Exception as e:
        print(f"[ERROR] get_ticker_info_sync({ticker}): {e}")
        raise HTTPException(status_code=404, detail=f"Unable to fetch info for {ticker}")


async def get_ticker_info_async(ticker: str) -> Dict[str, Any]:
    """Async wrapper for ticker info."""
    return await asyncio.to_thread(get_ticker_info_sync, ticker)


# ===============================
#            PRICE
# ===============================

async def get_latest_price(ticker: str) -> float:
    """Returns the latest closing price (async)."""
    df = await fetch_stock_data_async(ticker, period="1d", interval="1d")
    try:
        return float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"[ERROR] get_latest_price({ticker}): {e}")
        raise HTTPException(status_code=404, detail=f"Could not determine latest price for {ticker}")


# ===============================
#            NEWS
# ===============================

def get_stock_news_sync(ticker: str) -> List[dict]:
    """Synchronous wrapper to fetch news from yfinance; returns list of dicts or []"""
    try:
        t = yf.Ticker(ticker)
        raw_news = getattr(t, "news", None) or []
        # standardize to list of dicts with title/summary/url/published
        cleaned = []
        for item in raw_news:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("headline") or ""
            if not title or len(title.strip()) < 5:
                continue
            cleaned.append({
                "title": title,
                "summary": item.get("summary") or item.get("description") or "",
                "url": item.get("link") or item.get("url") or "",
                "providerPublishTime": item.get("providerPublishTime") or item.get("published"),
                "publisher": item.get("publisher") or item.get("source") or ""
            })
        return cleaned
    except Exception as e:
        print(f"[ERROR] get_stock_news_sync({ticker}): {e}")
        return []

async def get_stock_news_async(ticker: str) -> List[dict]:
    return await asyncio.to_thread(get_stock_news_sync, ticker)
