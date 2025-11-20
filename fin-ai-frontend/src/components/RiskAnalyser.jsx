//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/RiskAnalyser.jsx
"use client";
import React, { useState } from 'react';
import styles from '@/styles/RiskAnalyser.module.css';

export default function RiskAnalyser() {
  const [ticker, setTicker] = useState('');
  const [analysis, setAnalysis] = useState(null);
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
    setAnalysis(null);
    setError('');

    try {
      const response = await fetch(
        `${BASE_URL}/api/stock/risk/${ticker.toUpperCase()}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch risk analysis.');
      }
      
      setAnalysis(data);
    } catch (err) {
      setError(err.message || 'Network error or stock not found.');
      console.error('Risk analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'Very High': return styles.veryHigh;
      case 'High': return styles.high;
      case 'Moderate': return styles.moderate;
      case 'Low': return styles.low;
      default: return '';
    }
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.heading}>Stock Risk Analyser</h2>
      
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Enter Stock Ticker (e.g., AAPL, GOOGL)"
          className={styles.inputField}
          disabled={loading}
          required
        />
        <button 
          type="submit" 
          disabled={loading || !ticker.trim()} 
          className={styles.submitButton}
        >
          {loading ? 'Analysing...' : 'Analyse Risk'}
        </button>
      </form>

      {error && <p className={styles.errorMessage}>Error: {error}</p>}

      {analysis && (
        <div className={styles.resultsContainer}>
          <div className={`${styles.riskScoreCard} ${getRiskColor(analysis.risk_level)}`}>
            <h3 className={styles.riskTitle}>{analysis.ticker} Risk Profile</h3>
            <p className={styles.riskLevel}>
              Risk Level: 
              <span className={styles.riskLevelText}> {analysis.risk_level}</span>
            </p>
            <p className={styles.score}>Risk Score (1-100): {analysis.risk_score}</p>
          </div>

          <div className={styles.detailsCard}>
            <h4 className={styles.cardTitle}>Detailed Metrics</h4>
            <p>Current Price: <strong>${analysis.price?.toFixed(2) ?? 'N/A'}</strong></p>
            <p>Annual Volatility: <strong>{(analysis.volatility * 100).toFixed(2)}%</strong></p>
            <p>Beta: <strong>{analysis.beta?.toFixed(2) ?? 'N/A'}</strong></p>
            <p>Your Salary: <strong>${analysis.user_salary?.toLocaleString() ?? 'N/A'}</strong></p>
          </div>
          
          <div className={styles.suggestionCard}>
            <h4 className={styles.cardTitle}>Investment Suggestions</h4>
            <p className={styles.suggestionMessage}>{analysis.suggestion_message}</p>
            {analysis.suggested_stocks && analysis.suggested_stocks.length > 0 ? (
              <ul className={styles.suggestionList}>
                {analysis.suggested_stocks.map((stock, index) => (
                  <li key={index} className={styles.suggestionItem}>
                    <strong>{stock.ticker}</strong> ({stock.name}) - 
                    Price: ${stock.price?.toFixed(2) ?? 'N/A'} 
                    (Beta: {stock.beta?.toFixed(2) ?? 'N/A'})
                  </li>
                ))}
              </ul>
            ) : (
              <p>No alternative suggestions available at this time.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}