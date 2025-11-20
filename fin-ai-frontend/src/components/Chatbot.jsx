///Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/Chatbot.jsx
"use client";
import React, { useState, useRef, useEffect } from 'react';
import styles from '@/styles/Chatbot.module.css';

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchUserProfile();
    loadInitialMessage();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/api/chatbot/user-profile`,
        {
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUserProfile(data);
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const loadInitialMessage = () => {
    setMessages([
      {
        role: 'assistant',
        content: `Hello! 👋 I'm your personalized Financial AI Assistant. I have access to your profile and can provide tailored advice on:\n\n• Stock analysis and recommendations\n• Personal investment strategies\n• Portfolio management\n• Financial planning based on your salary and goals\n• Real-time market data\n\nHow can I help you today?`
      }
    ]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message to chat
    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/api/chatbot/query`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({ 
            message: userMessage,
            conversation_history: messages.slice(-10) // Last 10 messages for context
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      // Add assistant response to chat
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        stock_data: data.stock_data,
        timestamp: data.timestamp
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again or check your connection.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetRecommendations = async () => {
    setShowRecommendations(true);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000'}/api/chatbot/recommendations`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get recommendations');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.recommendations,
        isRecommendation: true
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I couldn\'t generate recommendations. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
      setShowRecommendations(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    loadInitialMessage();
  };

  const quickPrompts = [
    "Analyze AAPL stock for me",
    "What should I invest in based on my profile?",
    "Help me create a monthly budget",
    "Suggest tax-saving investments",
    "Portfolio diversification advice"
  ];

  const handleQuickPrompt = (prompt) => {
    setInput(prompt);
  };

  return (
    <div className={styles.chatbotContainer}>
      <div className={styles.chatHeader}>
        <div className={styles.headerContent}>
          <h2>Financial AI Assistant</h2>
          {userProfile && (
            <span className={styles.userGreeting}>
              Personalized for {userProfile.name}
            </span>
          )}
        </div>
        <div className={styles.headerActions}>
          <button 
            onClick={handleGetRecommendations} 
            className={styles.recommendButton}
            disabled={isLoading}
          >
            💡 Get Investment Recommendations
          </button>
          <button onClick={clearChat} className={styles.clearButton}>
            🗑️ Clear Chat
          </button>
        </div>
      </div>

      {messages.length === 1 && (
        <div className={styles.quickPromptsContainer}>
          <p className={styles.quickPromptsTitle}>Quick prompts to get started:</p>
          <div className={styles.quickPrompts}>
            {quickPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleQuickPrompt(prompt)}
                className={styles.quickPromptButton}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <div className={styles.messagesContainer}>
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`${styles.message} ${styles[message.role]}`}
          >
            <div className={styles.messageContent}>
              <div className={styles.messageIcon}>
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className={styles.messageText}>
                {message.content}
                
                {/* Display stock data if available */}
                {message.stock_data && Object.keys(message.stock_data).length > 0 && (
                  <div className={styles.stockDataContainer}>
                    {Object.entries(message.stock_data).map(([symbol, data]) => (
                      <div key={symbol} className={styles.stockCard}>
                        <h4>{symbol}</h4>
                        <div className={styles.stockDetails}>
                          <div className={styles.stockRow}>
                            <span>Current Price:</span>
                            <strong>${data.current_price}</strong>
                          </div>
                          <div className={styles.stockRow}>
                            <span>Day Range:</span>
                            <span>${data.day_low} - ${data.day_high}</span>
                          </div>
                          <div className={styles.stockRow}>
                            <span>52W Range:</span>
                            <span>${data.fifty_two_week_low} - ${data.fifty_two_week_high}</span>
                          </div>
                          {data.pe_ratio !== 'N/A' && (
                            <div className={styles.stockRow}>
                              <span>P/E Ratio:</span>
                              <span>{data.pe_ratio}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className={`${styles.message} ${styles.assistant}`}>
            <div className={styles.messageContent}>
              <div className={styles.messageIcon}>🤖</div>
              <div className={styles.messageText}>
                <div className={styles.typingIndicator}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className={styles.inputForm}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about stocks, investments, budgeting, or financial planning..."
          className={styles.input}
          rows="1"
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className={styles.sendButton}
          disabled={isLoading || !input.trim()}
        >
          {isLoading ? '⏳' : '📤'} Send
        </button>
      </form>
    </div>
  );
}