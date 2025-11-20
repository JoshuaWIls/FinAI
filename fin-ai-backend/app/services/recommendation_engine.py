# /app/services/recommendation_engine.py
from app.services.risk_service import generate_risk_profile
from app.services.yfinance_service import get_latest_price
from app.models import RiskProfile
from fastapi import HTTPException

async def get_recommendation(ticker: str, user_salary: float) -> dict:
    """
    Generates a buy/sell/hold recommendation.
    Uses async calls and awaits risk profile + latest price.
    """
    try:
        # Ensure inputs
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker required")

        # Get risk profile (async)
        risk: RiskProfile = await generate_risk_profile(ticker, user_salary)

        # Get latest price
        price = await get_latest_price(ticker)

        # Decide action from risk level
        rl = risk.risk_level.lower()
        if rl in ("low",):
            action = "BUY"
        elif rl in ("moderate", "medium"):
            action = "HOLD"
        else:
            action = "SELL"

        return {
            "ticker": ticker.upper(),
            "current_price": float(price),
            "risk_score": float(risk.risk_score),
            "risk_level": risk.risk_level,
            "recommendation": action,
            "note": risk.suggestion_message
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_recommendation({ticker}): {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendation")
