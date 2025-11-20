# /app/services/risk_service.py
import numpy as np
import asyncio
import random
from fastapi import HTTPException
from app.models import RiskProfile, SuggestedStock
from app.services.yfinance_service import (
    get_ticker_info_async,
    fetch_stock_data_async,
)

# Dynamic pools (expandable)
HIGH_VOL_STOCKS = [
    "TSLA","NVDA","COIN","AMD","SHOP","SQ","META","NFLX","PLTR","AFRM",
    "RIVN","SNAP","UBER","ABNB","CRWD","DDOG","ROKU","LI"
]
MED_VOL_STOCKS = [
    "AAPL","MSFT","AMZN","GOOG","V","MA","JPM","COST","AVGO","ORCL",
    "HD","ADBE","INTC","CSCO","QCOM","TXN","DIS"
]
LOW_VOL_STOCKS = [
    "PG","JNJ","KO","MCD","PEP","MRK","WMT","UNH","HD","COST",
    "CVS","T","VZ","PFE"
]

async def get_stock_metrics(ticker: str) -> dict:
    """Fetch history and compute volatility & beta with robust fallback."""
    try:
        history = await fetch_stock_data_async(ticker, period="1y", interval="1d")
        if history is None or history.empty:
            raise HTTPException(status_code=404, detail="No historical data found")

        history["Daily_Return"] = history["Close"].pct_change()
        volatility = history["Daily_Return"].std() * np.sqrt(252)
        volatility = float(volatility) if not np.isnan(volatility) else 0.0

        info = await get_ticker_info_async(ticker)
        price = info.get("last_price") or float(history["Close"].iloc[-1])
        beta = info.get("beta") or 1.0
        try:
            beta = float(beta)
        except:
            beta = 1.0

        return {"price": float(price), "beta": beta, "volatility": float(volatility)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] get_stock_metrics({ticker}): {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock metrics")


async def generate_risk_profile(ticker: str, user_salary: float) -> RiskProfile:
    """Create a user-specific risk profile and dynamic suggestions."""
    if user_salary is None or user_salary <= 0:
        raise HTTPException(status_code=400, detail="User salary (CTC) is missing or invalid.")

    metrics = await get_stock_metrics(ticker)
    volatility = metrics["volatility"]
    beta = metrics["beta"]

    # Salary normalization
    MAX_SALARY_BENCHMARK = 300000.0
    salary_factor = 1 - min(user_salary, MAX_SALARY_BENCHMARK) / MAX_SALARY_BENCHMARK

    # Composite risk score
    risk_score = (volatility * 100 * 0.6) + (beta * 10 * 0.3) + (salary_factor * 25)
    risk_score = float(min(max(risk_score, 1.0), 99.0))

    # Risk level
    if risk_score > 75:
        risk_level = "Very High"
    elif risk_score > 55:
        risk_level = "High"
    elif risk_score > 35:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # --- Updated: Suggestion pool based on risk_score ---
    if risk_score > 70:
        suggestion_pool = HIGH_VOL_STOCKS + MED_VOL_STOCKS
    elif risk_score > 50:
        suggestion_pool = MED_VOL_STOCKS + LOW_VOL_STOCKS
    else:
        suggestion_pool = LOW_VOL_STOCKS

    # Remove input ticker from suggestions
    suggestion_pool = [tk for tk in suggestion_pool if tk.upper() != ticker.upper()]

    sample_count = min(len(suggestion_pool), 7)
    sampled = random.sample(suggestion_pool, sample_count)

    # Fetch metadata concurrently
    tasks = [get_ticker_info_async(tk) for tk in sampled]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    suggestions = []
    for i, res in enumerate(results):
        if isinstance(res, Exception) or res is None:
            continue
        price = res.get("last_price") or res.get("raw_info", {}).get("regularMarketPrice")
        if price is None:
            continue
        short_name = res.get("shortName") or sampled[i]
        beta_val = res.get("beta") or 1.0
        try:
            beta_val = float(beta_val)
        except:
            beta_val = 1.0
        suggestions.append(SuggestedStock(ticker=sampled[i], name=short_name, price=float(price), beta=beta_val))

    # Guarantee at least 3 suggestions
    if len(suggestions) < 3:
        fallback_pool = MED_VOL_STOCKS + LOW_VOL_STOCKS + HIGH_VOL_STOCKS
        for tk in random.sample(fallback_pool, min(10, len(fallback_pool))):
            try:
                info = await get_ticker_info_async(tk)
            except:
                continue
            price = info.get("last_price") or info.get("raw_info", {}).get("regularMarketPrice")
            if price is None:
                continue
            suggestions.append(SuggestedStock(ticker=tk, name=info.get("shortName") or tk, price=float(price), beta=(info.get("beta") or 1.0)))
            if len(suggestions) >= 3:
                break

    # Last-chance fallback
    if len(suggestions) < 3:
        hardcoded = [
            SuggestedStock(ticker="AAPL", name="Apple Inc.", price=0.0, beta=1.0),
            SuggestedStock(ticker="MSFT", name="Microsoft Corp.", price=0.0, beta=1.0),
            SuggestedStock(ticker="GOOGL", name="Alphabet Inc.", price=0.0, beta=1.0),
        ]
        suggestions.extend(hardcoded[: (3 - len(suggestions))])

    message = f"Volatility: {round(volatility * 100, 2)}%. Suggested based on your risk profile."

    return RiskProfile(
        ticker=ticker.upper(),
        price=metrics["price"],
        volatility=metrics["volatility"],
        beta=beta,
        user_salary=user_salary,
        risk_score=round(risk_score, 2),
        risk_level=risk_level,
        suggestion_message=message,
        suggested_stocks=suggestions[:5]
    )
