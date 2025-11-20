///Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/AuthForm.jsx
"use client"
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import styles from '@/styles/AuthForm.module.css';

export default function AuthForm({ type }) {
  const [formData, setFormData] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  
  const isRegister = type === 'register';
  const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000';

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    const url = isRegister ? `${BASE_URL}/api/auth/register` : `${BASE_URL}/api/auth/login`;
    if (!formData.email || !formData.password) {
        setLoading(false);
        return setError('Email and Password are required.');
    }
    
    if (isRegister) {
      if (!formData.name || !formData.dateOfBirth || !formData.occupation || !formData.currentSalary) {
        setLoading(false);
        return setError('All registration fields are required.');
      }
      if (!/\S+@\S+\.\S+/.test(formData.email)) {
        setLoading(false);
        return setError('Please enter a valid email address.');
      }
      if (formData.password.length < 6) {
        setLoading(false);
        return setError('Password must be at least 6 characters long.');
      }
    }
    
    try {
      console.log(`🚀 Attempting ${isRegister ? 'registration' : 'login'} to:`, url);
      
      // Add timeout controller
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(formData),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      console.log('📡 Response status:', response.status);

      const data = await response.json();
      console.log('📦 Response data:', data);

      if (!response.ok) {
        setError(data.detail || data.message || 'An error occurred.');
        setLoading(false);
        return;
      }
      
      setSuccess(data.message);
      
      if (!isRegister) {
        // Login successful - redirect to dashboard
        setTimeout(() => {
          router.push('/dashboard');
          router.refresh();
        }, 500);
      } else {
        // Registration successful - redirect to login
        setTimeout(() => {
          router.push('/?form=login');
        }, 1500);
      }

    } catch (err) {
      console.error('❌ Auth error:', err);
      
      if (err.name === 'AbortError') {
        setError('Request timeout. Please check your connection and try again.');
      } else if (err.message.includes('Failed to fetch')) {
        setError(`Cannot connect to server at ${BASE_URL}. Please ensure the backend is running.`);
      } else {
        setError(`Network error: ${err.message}`);
      }
      
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.companyLogo}>FinAI</div>
        <h2 className={styles.formTitle}>
          {isRegister ? 'Create Your Account' : 'Welcome Back!'}
        </h2>
        
        {error && <p className={styles.errorMessage}>{error}</p>}
        {success && <p className={styles.successMessage}>{success}</p>}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <input 
                name="name" 
                type="text" 
                value={formData.name || ''} 
                onChange={handleChange} 
                placeholder="Full Name" 
                required 
                className={styles.inputField} 
              />
              <input 
                name="dateOfBirth" 
                type="date" 
                value={formData.dateOfBirth || ''} 
                onChange={handleChange} 
                required 
                className={styles.inputField} 
              />
              <input 
                name="occupation" 
                type="text" 
                value={formData.occupation || ''} 
                onChange={handleChange} 
                placeholder="Occupation" 
                required 
                className={styles.inputField} 
              />
              <input 
                name="currentSalary" 
                type="number" 
                value={formData.currentSalary || ''} 
                onChange={handleChange} 
                placeholder="Current Salary (CTC)" 
                required 
                className={styles.inputField} 
              />
            </>
          )}

          <input 
            name="email" 
            type="email" 
            value={formData.email || ''} 
            onChange={handleChange} 
            placeholder="Email Address" 
            required 
            className={styles.inputField} 
          />
          <input 
            name="password" 
            type="password" 
            value={formData.password || ''} 
            onChange={handleChange} 
            placeholder="Password" 
            required 
            className={styles.inputField} 
          />
          
          <button 
            type="submit" 
            className={styles.submitButton} 
            disabled={loading}
          >
            {loading 
              ? (isRegister ? 'Signing Up...' : 'Logging In...') 
              : (isRegister ? 'Sign Up' : 'Log In')
            }
          </button>
        </form>

        <p className={styles.switchText}>
          {isRegister ? "Already have an account? " : "Don't have an account? "}
          <a 
            href={isRegister ? "/?form=login" : "/?form=register"} 
            className={styles.switchLink}
          > 
            {isRegister ? "Log In" : "Sign Up"} 
          </a>
        </p>
      </div>
    </div>
  );
}