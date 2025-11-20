# app/routes/sentiment.py
from fastapi import APIRouter, HTTPException, Query
from app.services.sentiment_service import get_sentiment
from app.models import SentimentResponse

router = APIRouter(tags=["sentiment"])

@router.get("/analyze", response_model=SentimentResponse)
async def analyze_text(text: str = Query(..., min_length=1)):
    try:
        sentiment = get_sentiment(text)
        return {
            "symbol": None,
            "text": text,
            "sentiment": sentiment.value,
            "score": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
