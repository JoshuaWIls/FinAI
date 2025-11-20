//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/components/LogoutButton.jsx
'use client'
import React from 'react';
import { useRouter } from 'next/navigation';

export default function LogoutButton() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
      });

      if (response.ok) {
        router.push('/');
      } else {
        // Handle logout error (e.g., alert or message)
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('Network error during logout:', error);
    }
  };

  return (
    <button 
      onClick={handleLogout} 
      className="p-2 bg-red-500 text-white rounded hover:bg-red-600"
    >
      Log Out
    </button>
  );
}