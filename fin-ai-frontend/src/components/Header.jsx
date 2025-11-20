// /Users/jwils/Developer/code/7th sem project Finance AI/financialai/src/components/Header.jsx
"use client";
import React from 'react';
import styles from '@/styles/Header.module.css'; 
import { useRouter } from 'next/navigation';

export default function Header({ userName }) {
  const router = useRouter();
  const handleLogout = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/api/auth/logout`, {
        method: 'POST',
      });

      if (response.ok) {
        router.push('/');
      } else {
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('Network error during logout:', error);
    }
  };
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.logo}>
          <a href="/dashboard">Fin-AI</a>
        </div>
        <nav className={styles.nav}>
          <ul className={styles.navList}>
            {/* UPDATED LINKS */}
            <li className={styles.navItem}><a href="/dashboard/risk-analyser">Risk Analyser</a></li>
            <li className={styles.navItem}><a href="/dashboard/stock-prediction">Stock Prediction</a></li>
            <li className={styles.navItem}><a href="/dashboard/chatbot">ChatBot</a></li>
          </ul>
        </nav>
        <div className={styles.userSection}>
          <span className={styles.userName}>Hello, {userName}</span>
          {/* UPDATED LOGOUT BUTTON/LINK */}
          <a href="#" onClick={handleLogout} className={styles.logoutLink}>Logout</a>
        </div>
      </div>
    </header>
  );
}