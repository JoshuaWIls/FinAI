# /app/routes/stock_prediction.py
from fastapi import APIRouter, HTTPException, Depends, Request
import os
import joblib
import asyncio
import numpy as np
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from scipy.special import softmax

from app.services.yfinance_service import fetch_stock_data_async, get_stock_news_async
from app.services.auth_service import get_current_user
from app.services.mongo_service import get_user_by_id_str
from app.models import UserInDB

router = APIRouter(tags=["stock_prediction"])

MODEL_PATH = os.getenv("PREDICTION_MODEL_PATH", "./models/stock_predictor.joblib")

# caching globals
_model_data = None
_sentiment_tokenizer = None
_sentiment_model = None


def load_model():
    """Load trained model and scaler (cached)."""
    global _model_data
    if _model_data is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Prediction model not found at {MODEL_PATH}")
        _model_data = joblib.load(MODEL_PATH)
    return _model_data


def load_sentiment_model():
    """Load FinBERT (cached)."""
    global _sentiment_tokenizer, _sentiment_model
    if _sentiment_tokenizer is None or _sentiment_model is None:
        _sentiment_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        _sentiment_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        _sentiment_model.eval()
    return _sentiment_tokenizer, _sentiment_model


def get_sentiment_score_sync(text: str) -> float:
    """Synchronous FinBERT inference for a string; returns score in [-1,1]."""
    if not text or not text.strip():
        return 0.0
    try:
        tokenizer, model = load_sentiment_model()
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            scores = outputs.logits[0].detach().cpu().numpy()
            probs = softmax(scores)
        # positive - negative
        return float(probs[2] - probs[0])
    except Exception as e:
        print(f"[WARN] FinBERT local inference failed: {e}")
        return 0.0


async def get_realtime_sentiment(symbol: str) -> float:
    """Aggregate sentiment from yfinance news (async) using FinBERT."""
    try:
        raw_news = await get_stock_news_async(symbol)
        if not raw_news:
            return 0.0
        sentiments = []
        for n in raw_news[:10]:
            text = f"{n.get('title','')} {n.get('summary','')}"
            s = await asyncio.to_thread(get_sentiment_score_sync, text)
            sentiments.append(s)
        return float(np.mean(sentiments)) if sentiments else 0.0
    except Exception as e:
        print(f"[WARN] get_realtime_sentiment({symbol}) failed: {e}")
        return 0.0


def calculate_technical_indicators(df):
    """Add technical indicator columns (mutates df)."""
    df = df.copy()
    df['Returns'] = df['Close'].pct_change()
    df['SMA_5'] = df['Close'].rolling(window=5).mean()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Volatility'] = df['Returns'].rolling(window=20).std()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
    df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
    df['Momentum'] = df['Close'] - df['Close'].shift(10)
    df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
    return df


def recommend_action(prediction_proba, sentiment: float, rsi: float) -> str:
    """Map model probability + sentiment + RSI to action."""
    try:
        confidence = max(prediction_proba)
        prediction = 1 if prediction_proba[1] > prediction_proba[0] else 0
        if prediction == 1 and confidence > 0.75 and sentiment > 0.3 and rsi < 70:
            return "Strong Buy"
        elif prediction == 1 and confidence > 0.60 and sentiment > 0:
            return "Buy"
        elif prediction == 0 and confidence > 0.75 and sentiment < -0.3 and rsi > 30:
            return "Strong Sell"
        elif prediction == 0 and confidence > 0.60 and sentiment < 0:
            return "Sell"
        else:
            return "Hold"
    except Exception:
        return "Hold"


@router.get("/{symbol}")
async def predict_stock(symbol: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Endpoint to make stock predictions using saved model + sentiment + tech indicators."""
    symbol = symbol.upper()
    try:
        model_data = load_model()
        technical_model = model_data.get("technical_model")
        scaler = model_data.get("scaler")

        # fetch market data
        df = await fetch_stock_data_async(symbol, period="3mo", interval="1d")
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Insufficient market data")

        df = calculate_technical_indicators(df)
        latest = df.iloc[-1]

        # sentiment
        sentiment_score = await get_realtime_sentiment(symbol)

        # build features
        features = np.array([[
            latest.get('Returns', 0.0),
            latest.get('SMA_5', 0.0),
            latest.get('SMA_10', 0.0),
            latest.get('SMA_20', 0.0),
            latest.get('EMA_5', 0.0),
            latest.get('EMA_20', 0.0),
            latest.get('Volatility', 0.0),
            latest.get('RSI', 50.0),
            latest.get('MACD', 0.0),
            latest.get('Signal_Line', 0.0),
            latest.get('BB_Width', 0.0),
            latest.get('Volume_Ratio', 1.0),
            latest.get('Momentum', 0.0),
            latest.get('ROC', 0.0),
            sentiment_score
        ]])

        # scale and predict
        features_scaled = scaler.transform(features)
        prediction_proba = technical_model.predict_proba(features_scaled)[0]

        expected_return = (prediction_proba[1] * 0.05) - (prediction_proba[0] * 0.03)
        recommendation = recommend_action(prediction_proba, sentiment_score, float(latest.get('RSI', 50.0)))

        return {
            "symbol": symbol,
            "prediction": {
                "direction": "Bullish" if prediction_proba[1] > prediction_proba[0] else "Bearish",
                "confidence": float(max(prediction_proba) * 100),
                "probability_up": float(prediction_proba[1] * 100),
                "probability_down": float(prediction_proba[0] * 100),
                "expected_return_percent": float(expected_return * 100)
            },
            "sentiment_analysis": {
                "news_sentiment_score": float(sentiment_score),
                "sentiment_label": "Positive" if sentiment_score > 0.1 else "Negative" if sentiment_score < -0.1 else "Neutral"
            },
            "technical_indicators": {
                "current_price": float(latest.get('Close', 0.0)),
                "rsi": float(latest.get('RSI', 50.0)),
                "macd": float(latest.get('MACD', 0.0)),
                "volatility": float(latest.get('Volatility', 0.0) * 100),
                "volume_ratio": float(latest.get('Volume_Ratio', 1.0))
            },
            "recommendation": recommendation,
            "recommendation_explanation": "",  # keep simple or call get_explanation
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] predict_stock({symbol}): {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")
