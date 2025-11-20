from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta
import os
import requests
import yfinance as yf
import numpy as np
import pandas as pd

from app.models import NewsItemOut
from app.services.sentiment_service import get_sentiment
from app.services.yfinance_service import get_ticker_info_async, get_stock_news_async

router = APIRouter(tags=["stock"])

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

@router.get("/{ticker}")
async def get_stock_data_endpoint(
    ticker: str,
    period: str = Query("1mo", description="Period: 5d, 1mo, 3mo, 1y"),
    interval: str = Query("1d", description="Interval: 1h, 1d, 1wk")
):
    """Fetch stock price data for charts"""
    try:
        ticker = ticker.upper()
        print(f"📊 Fetching {ticker} data: period={period}, interval={interval}")
        
        # Download data
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for '{ticker}'")
        
        print(f"   DataFrame shape: {df.shape}")
        print(f"   DataFrame columns: {df.columns.tolist()}")
        print(f"   DataFrame index: {df.index.name}")
        
        data = []
        
        # Iterate through the DataFrame
        for idx, row in df.iterrows():
            try:
                # Handle timestamp (idx is the timestamp)
                if hasattr(idx, 'timestamp'):
                    unix_ts = int(idx.timestamp())
                else:
                    unix_ts = int(pd.Timestamp(idx).timestamp())
                
                # Handle Close price (works for both single and multi-ticker downloads)
                if 'Close' in df.columns:
                    close_val = row['Close']
                    # If it's a Series (multi-ticker), get first value
                    if isinstance(close_val, pd.Series):
                        close_val = close_val.iloc[0]
                    close_price = float(close_val)
                else:
                    print(f"⚠️ 'Close' not in columns: {df.columns.tolist()}")
                    continue
                
                # Handle Volume
                if 'Volume' in df.columns:
                    vol_val = row['Volume']
                    if isinstance(vol_val, pd.Series):
                        vol_val = vol_val.iloc[0]
                    volume = int(vol_val) if not pd.isna(vol_val) else 0
                else:
                    volume = 0
                
                data.append({
                    "timestamp": unix_ts,
                    "close": close_price,
                    "volume": volume
                })
                
            except Exception as e:
                print(f"⚠️ Error processing row at {idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not data:
            print(f"❌ No data points processed from {len(df)} rows")
            raise HTTPException(status_code=404, detail=f"Could not process data for '{ticker}'")
        
        print(f"✅ Successfully processed {len(data)} data points for {ticker}")
        return {"data": data, "ticker": ticker, "period": period, "interval": interval}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching stock data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for '{ticker}': {str(e)}")

# -------------------- Stock Core Metrics --------------------
def get_stock_data(ticker: str) -> dict:
    """Fetch core stock metrics: last price, beta, volatility."""
    try:
        t = yf.Ticker(ticker)
        fast = getattr(t, "fast_info", {}) or {}

        price = fast.get("last_price") or fast.get("regularMarketPrice")
        if price is None:
            hist = t.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        if price is None:
            raise HTTPException(status_code=404, detail=f"No live price for {ticker}")

        hist1y = t.history(period="1y")
        if hist1y is not None and len(hist1y) > 1:
            hist1y["Daily_Return"] = hist1y["Close"].pct_change()
            volatility = float(hist1y["Daily_Return"].std() * np.sqrt(252))
        else:
            volatility = 0.0

        beta = fast.get("beta") or getattr(t, "info", {}).get("beta") or 1.0

        return {"price": float(price), "beta": float(beta), "volatility": float(volatility)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_stock_data({ticker}): {e}")
        raise HTTPException(status_code=404, detail=f"Could not fetch market data for {ticker}")


# -------------------- Stock History Endpoint --------------------
@router.get("/history/{ticker}")
async def stock_history(
    ticker: str,
    period: str = Query("1mo", description="Period: 7d, 1mo, 3mo, 1y"),
    interval: str = Query("1d", description="Interval: 1d, 1wk")
):
    """
    Fetch historical stock prices.
    Returns: date, close price, volume, beta, volatility.
    """
    ticker = ticker.upper()
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data for {ticker}")

        hist["Daily_Return"] = hist["Close"].pct_change()
        volatility = float(hist["Daily_Return"].std() * np.sqrt(252))
        beta = getattr(t, "fast_info", {}).get("beta") or getattr(t, "info", {}).get("beta") or 1.0

        data = []
        for idx, row in hist.iterrows():
            data.append({
                "date": idx.isoformat(),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
                "beta": float(beta),
                "volatility": float(volatility),
            })
        return data

    except Exception as e:
        print(f"[ERROR] stock_history({ticker}): {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock history")


# -------------------- Stock News Endpoint --------------------
def fetch_news_from_newsapi(ticker: str, company_name: str = None) -> List[dict]:
    """Fetch news from NewsAPI.org (if key present)."""
    if not NEWSAPI_KEY:
        return []

    try:
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=7)
        query = ticker if not company_name else f"{ticker} OR {company_name}"
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": NEWSAPI_KEY,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d")
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code != 200:
            print(f"[WARN] NewsAPI returned {resp.status_code}")
            return []

        items = []
        for a in resp.json().get("articles", []):
            title = a.get("title") or ""
            if len(title.strip()) < 5:
                continue
            items.append({
                "title": title,
                "description": a.get("description") or "",
                "url": a.get("url") or "",
                "source": a.get("source", {}).get("name", "Unknown"),
                "publishedAt": a.get("publishedAt") or datetime.utcnow().isoformat()
            })
        return items

    except Exception as e:
        print(f"[ERROR] fetch_news_from_newsapi: {e}")
        return []


@router.get("/news/{ticker}", response_model=List[NewsItemOut])
async def get_stock_news(ticker: str):
    ticker = ticker.upper()
    try:
        company_name = None
        try:
            info = await get_ticker_info_async(ticker)
            company_name = info.get("shortName")
        except:
            pass

        all_news = []
        if NEWSAPI_KEY:
            all_news.extend(fetch_news_from_newsapi(ticker, company_name))

        yf_news = await get_stock_news_async(ticker)
        for item in yf_news:
            title = item.get("title") or ""
            if len(title.strip()) < 5:
                continue
            all_news.append({
                "title": title,
                "description": item.get("summary") or "",
                "url": item.get("url") or "",
                "source": item.get("publisher") or "Unknown",
                "publishedAt": item.get("providerPublishTime") or item.get("published") or datetime.utcnow().isoformat()
            })

        # dedupe by title
        seen = set()
        unique = []
        for it in all_news:
            t_lower = it.get("title", "").lower().strip()
            if not t_lower or t_lower in seen:
                continue
            seen.add(t_lower)
            unique.append(it)

        # limit to 10 and annotate sentiment
        unique = unique[:10]
        out = []
        for u in unique:
            text = f"{u.get('title','')} {u.get('description','')}".strip()
            sentiment = get_sentiment(text) if text else "Neutral"
            s_val = sentiment.value if hasattr(sentiment, "value") else str(sentiment)
            published = u.get("publishedAt")
            if not isinstance(published, str):
                published = str(published)
            out.append(NewsItemOut(
                headline=u.get("title"),
                summary=u.get("description"),
                source=u.get("source") or "Unknown",
                link=u.get("url") or "",
                sentiment=s_val,
                timestamp=published
            ))
        return out

    except Exception as e:
        print(f"[ERROR] get_stock_news route: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock news")
