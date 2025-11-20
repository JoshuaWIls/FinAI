"use client";
import React, { useState, useEffect } from 'react';
import Header from '@/components/Header';
import Chatbot from '@/components/Chatbot';
import styles from '@/styles/ChatbotPage.module.css';

export default function ChatbotPage() {
  const [userName, setUserName] = useState("User");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/api/chatbot/user-profile`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUserName(data.name || "User");
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className={styles.pageContainer}>
        <div className={styles.loadingContainer}>
          <div className={styles.loader}></div>
          <p>Loading your personalized assistant...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.pageContainer}>
      <Header userName={userName} />
      <main className={styles.mainContent}>
        <div className={styles.chatbotWrapper}>
          <Chatbot />
        </div>
      </main>
    </div>
  );
}