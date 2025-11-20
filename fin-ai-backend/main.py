# /Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import yfinance as yf
import datetime as dt

# Load environment variables
load_dotenv()

# Core router
from app.routes import auth

# Router placeholders (load safely)
news_router = None
risk_analysis_router = None
sentiment_router = None
stock_prediction_router = None
stock_router = None
chatbot_router = None

# ---- Safe Dynamic Router Imports ----
try:
    from app.routes import news
    news_router = news.router
    print("✅ News router loaded successfully")
except Exception as e:
    print(f"⚠️ News router not loaded: {e}")

try:
    from app.routes import risk_analysis
    risk_analysis_router = risk_analysis.router
    print("✅ Risk analysis router loaded successfully")
except Exception as e:
    print(f"⚠️ Risk analysis router not loaded: {e}")

try:
    from app.routes import sentiment
    sentiment_router = sentiment.router
    print("✅ Sentiment router loaded successfully")
except Exception as e:
    print(f"⚠️ Sentiment router not loaded: {e}")

try:
    from app.routes import stock_prediction
    stock_prediction_router = stock_prediction.router
    print("✅ Stock prediction router loaded successfully")
except Exception as e:
    print(f"⚠️ Stock prediction router not loaded: {e}")

try:
    from app.routes import stock
    stock_router = stock.router
    print("✅ Stock router loaded successfully")
    print(f"   Stock router has {len(stock_router.routes)} routes")
except Exception as e:
    print(f"⚠️ Stock router not loaded: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routes import chatbot
    chatbot_router = chatbot.router
    print("✅ Chatbot router loaded successfully")
    print(f"   Chatbot router has {len(chatbot_router.routes)} routes")
except Exception as e:
    print(f"⚠️ Chatbot router not loaded: {e}")
    import traceback
    traceback.print_exc()


# ---- Lifespan (MongoDB Connection) ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.mongo_service import client
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Make sure your MONGODB_URI is correct in .env")
    yield
    client.close()
    print("👋 MongoDB connection closed")


# ---- Initialize App ----
app = FastAPI(
    title="FinAI Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# ---- Session Middleware (MUST BE BEFORE CORS) ----
app.add_middleware(
    SessionMiddleware, 
    secret_key="your-secret-key-here-change-in-production",  # TODO: Move to .env in production
    max_age=3600 * 24 * 7,  # Session expires in 7 days
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Register Routers ----
# Always load Authentication
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
print("✅ Auth router registered at /api/auth")

# Load optional modules
if news_router:
    app.include_router(news_router, prefix="/api/news", tags=["News"])
    print("✅ News router registered at /api/news")

if sentiment_router:
    app.include_router(sentiment_router, prefix="/api/sentiment", tags=["Sentiment"])
    print("✅ Sentiment router registered at /api/sentiment")

# Register MORE SPECIFIC stock routes FIRST
if risk_analysis_router:
    app.include_router(risk_analysis_router, prefix="/api/stock/risk", tags=["Risk Analysis"])
    print("✅ Risk analysis router registered at /api/stock/risk")

if stock_prediction_router:
    app.include_router(stock_prediction_router, prefix="/api/stock/predict", tags=["Stock Prediction"])
    print("✅ Stock prediction router registered at /api/stock/predict")

# Register GENERAL stock router LAST (to avoid conflicts)
if stock_router:
    app.include_router(stock_router, prefix="/api/stock", tags=["Stock"])
    print("✅ Stock router registered at /api/stock")
    # Print all stock routes for debugging
    for route in stock_router.routes:
        if hasattr(route, 'path'):
            print(f"   - {route.path} [{', '.join(route.methods)}]")
else:
    print("❌ Stock router NOT registered - router is None")

# Register Chatbot router
if chatbot_router:
    app.include_router(chatbot_router, prefix="/api/chatbot", tags=["Chatbot"])
    print("✅ Chatbot router registered at /api/chatbot")
    # Print all chatbot routes for debugging
    for route in chatbot_router.routes:
        if hasattr(route, 'path'):
            print(f"   - {route.path} [{', '.join(route.methods)}]")
else:
    print("❌ Chatbot router NOT registered - router is None")

# ---- Debug Routes Endpoint ----
@app.get("/debug/routes")
def list_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name
            })
    return sorted(routes, key=lambda x: x['path'])


# ---- Root & Health Endpoints ----
@app.get("/")
def root():
    return {
        "message": "🚀 FinAI Backend is running!",
        "version": "1.0.0",
        "auth": "enabled",
        "news": "enabled" if news_router else "disabled",
        "risk_analysis": "enabled" if risk_analysis_router else "disabled",
        "sentiment": "enabled" if sentiment_router else "disabled",
        "stock_prediction": "enabled" if stock_prediction_router else "disabled",
        "stock": "enabled" if stock_router else "disabled",
        "chatbot": "enabled" if chatbot_router else "disabled",
    }


@app.get("/health")
async def health_check():
    from app.services.mongo_service import client
    try:
        await client.admin.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    return {"status": "healthy", "database": db_status}


# ---- Run Server ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)