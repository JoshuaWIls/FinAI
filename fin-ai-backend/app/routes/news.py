# app/routes/news.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
import os
import requests
from app.services.sentiment_service import get_sentiment, SentimentResult
from app.models import SentimentResponse

router = APIRouter(tags=["news"])

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
if not NEWSAPI_KEY:
    # For production require a key; if you want to allow no-key mode, handle differently.
    raise RuntimeError("NEWSAPI_KEY environment variable is required for /news endpoints")

@router.get("/search", response_model=List[SentimentResponse])
async def search_news(symbol: str = Query(..., description="Ticker symbol, e.g. AAPL"), q: str = Query(None), page_size: int = 10):
    """
    Search news for a symbol (and optional q filter), analyze sentiment for each article headline.
    Uses NewsAPI (developer.key required).
    """
    symbol_upper = symbol.upper()
    query = f"{symbol_upper}"
    if q:
        query += f" {q}"

    params = {
        "q": query,
        "pageSize": page_size,
        "apiKey": NEWSAPI_KEY,
        "language": "en",
        "sortBy": "publishedAt"
    }
    resp = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch news")

    data = resp.json()
    articles = data.get("articles", [])[:page_size]
    results = []
    for a in articles:
        title = a.get("title") or ""
        desc = a.get("description") or ""
        text = f"{title}. {desc}"
        sentiment = get_sentiment(text)
        results.append({
            "symbol": symbol_upper,
            "text": text,
            "sentiment": sentiment.value,
            "score": None  # FinBERT wrapper returns only label currently; if you want score, extend service
        })

    return results
