//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/NewsFeed.jsx
"use client";
import React, { useState, useEffect } from 'react';
import styles from '@/styles/NewsFeed.module.css';

export default function NewsFeed() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'; 
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/news`); 

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error fetching news.' }));
          throw new Error(errorData.detail || 'Failed to fetch general news');
        }

        const data = await response.json();
        setNews(data);

      } catch (error) {
        console.error("Error fetching news:", error);
        setError(error.message || 'Could not connect to the financial news API.');
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  if (loading) {
    return <div className={styles.loading}>Loading news...</div>;
  }
  
  if (error) {
    return <div className={styles.newsContainer}><div className={styles.errorMessage}>Error: {error}</div></div>;
  }
  
  if (news.length === 0) {
    return <div className={styles.newsContainer}><div className={styles.noNews}>No financial news available at this time.</div></div>;
  }

  return (
    <div className={styles.newsContainer}>
      <h2 className={styles.newsHeading}>Current Financial News</h2>
      <div className={styles.newsGrid}>
        {news.map((item, index) => (
          <a 
            key={index} 
            href={item.url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className={styles.newsCard}
          >
            <h3 className={styles.newsHeadline}>{item.headline}</h3>
            <p className={styles.newsSummary}>{item.summary}</p>
            <div className={styles.newsMeta}>
              {}
              <span className={styles.newsSource}>{item.source}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}