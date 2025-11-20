///Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/StockPrediction.jsx
"use client";
import React, { useState } from 'react';
import styles from '@/styles/StockPrediction.module.css';

export default function StockPrediction() {
  const [ticker, setTicker] = useState('');
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticker.trim()) {
      setError('Please enter a valid ticker symbol');
      return;
    }

    setLoading(true);
    setNews([]);
    setError('');

    try {
      const response = await fetch(
        `${BASE_URL}/api/stock/news/${ticker.toUpperCase()}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch stock news and sentiment.');
      }

      const data = await response.json();
      
      console.log('Fetched news data:', data); // Debug log
      
      // Check if data is an array and has items
      if (Array.isArray(data) && data.length > 0) {
        setNews(data);
      } else {
        setError('No news available for this stock at the moment.');
      }
      
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message || 'Network error or stock news not found.');
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    if (!sentiment) return styles.neutral;
    
    const sentimentLower = sentiment.toLowerCase();
    
    if (sentimentLower === 'positive') return styles.positive;
    if (sentimentLower === 'negative') return styles.negative;
    return styles.neutral;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown date';
    
    try {
      // If timestamp is a number (Unix timestamp)
      if (typeof timestamp === 'number') {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // If timestamp is a string
      const date = new Date(timestamp);
      if (!isNaN(date.getTime())) {
        return date.toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'short', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      return 'Unknown date';
    } catch (error) {
      return 'Unknown date';
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.heading}>Stock Sentiment & Prediction News</h2>
      
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Enter Stock Ticker (e.g., AAPL, TSLA, NVDA)"
          className={styles.inputField}
          disabled={loading}
          required
        />
        <button 
          type="submit" 
          disabled={loading || !ticker.trim()} 
          className={styles.submitButton}
        >
          {loading ? 'Analysing...' : 'Get News & Sentiment'}
        </button>
      </form>

      {error && <p className={styles.errorMessage}>{error}</p>}

      {loading && (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Fetching latest news and analyzing sentiment...</p>
        </div>
      )}

      {!loading && news.length > 0 && (
        <div className={styles.newsGrid}>
          {news.map((item, index) => (
            <div key={index} className={styles.newsCard}>
              <h3 className={styles.headline}>
                {item.headline || 'No headline available'}
              </h3>
              
              <p className={styles.summary}>
                {item.summary || 'No summary available.'}
              </p>
              
              <div className={styles.meta}>
                <div className={styles.sourceInfo}>
                  <span className={styles.source}>
                    {item.source || 'Unknown'}
                  </span>
                  <span className={styles.timestamp}>
                    {formatTimestamp(item.timestamp)}
                  </span>
                </div>
                
                <span className={`${styles.sentimentPill} ${getSentimentColor(item.sentiment)}`}>
                  {item.sentiment || 'Neutral'}
                </span>
              </div>
              
              {item.link && (
                <a 
                  href={item.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className={styles.readMore}
                >
                  Read full article →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
      
      {!loading && !error && news.length === 0 && ticker && (
        <p className={styles.placeholder}>
          No news found for {ticker.toUpperCase()}. Try another ticker symbol.
        </p>
      )}
      
      {!loading && !error && news.length === 0 && !ticker && (
        <p className={styles.placeholder}>
          Enter a ticker symbol to see the latest news with FinBERT sentiment analysis.
        </p>
      )}
    </div>
  );
}