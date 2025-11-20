# app/services/sentiment_service.py
import subprocess
from enum import Enum

class SentimentResult(str, Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"

def query_ollama(prompt: str) -> str:
    """
    Calls the local Ollama model (llama3:instruct) using subprocess.
    Returns the model output as plain text.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3:instruct", prompt],
            capture_output=True,
            text=True,
            timeout=20,  # Increased timeout for longer financial texts
            check=True
        )
        output = result.stdout.strip()
        if not output:
            # Ollama returned empty string
            return "Neutral"
        return output
    except subprocess.TimeoutExpired:
        print("Ollama timeout, returning Neutral sentiment")
        return "Neutral"
    except Exception as e:
        print("Ollama sentiment analysis failed:", e)
        return "Neutral"

def get_sentiment(text: str) -> SentimentResult:
    """
    Returns Positive / Negative / Neutral even if Ollama crashes or times out.
    """
    if not text or not text.strip():
        return SentimentResult.NEUTRAL

    prompt = f"""
    Analyze the sentiment of the following financial text.
    Reply with one word only: Positive, Negative, or Neutral.

    Text: "{text}"
    """
    response = query_ollama(prompt).lower()

    if "positive" in response:
        return SentimentResult.POSITIVE
    if "negative" in response:
        return SentimentResult.NEGATIVE
    return SentimentResult.NEUTRAL

def analyze_latest_news(news_articles: list[dict]):
    """
    Receives a list of articles and performs sentiment analysis.
    Keeps timestamps as strings to avoid integer parsing errors.
    """
    # Sort by 'publishedAt' string if available
    news_articles = sorted(news_articles, key=lambda x: x.get("publishedAt", ""), reverse=True)
    latest_news = news_articles[:10]

    results = []
    for article in latest_news:
        text = article.get("description") or article.get("title", "")
        sentiment = get_sentiment(text)
        results.append({
            "title": article.get("title", ""),
            "publishedAt": article.get("publishedAt", ""),
            "sentiment": sentiment.value,
            "source": article.get("source", "Unknown"),
            "url": article.get("url", "")
        })
    return results
