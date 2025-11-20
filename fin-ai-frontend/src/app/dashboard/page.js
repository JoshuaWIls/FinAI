//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/dashboard/page.js
import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import Header from '@/components/Header';
import MarketOverview from '@/components/MarketOverview';
import '@/styles/globals.css';

// Function to get user data from the protected API route (Server-side fetch)
export async function getAuthenticatedUser() {
  const cookieStore =await cookies();
  const token = cookieStore.get('authToken');
  const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000';

  if (!token) {
    redirect('/'); 
  }

  const response =await fetch(`${BASE_URL}/api/auth/user`, {
    headers: {
      'Cookie': `authToken=${token.value}`, 
    },
    cache: 'no-store' 
  });

  if (!response.ok) {
    redirect('/'); 
  }

  return response.json();
}

export default async function DashboardPage() {
  let user;
  try {
    user = await getAuthenticatedUser();
  } catch (error) {
    throw error;
  }
  
  return (
    <>
      <Header userName={user.name} /> 
      
      <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <MarketOverview />
      </main>
    </>
  );
}