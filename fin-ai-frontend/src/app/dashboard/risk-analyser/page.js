//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/dashboard/risk-analyser/page.js
import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import Header from '@/components/Header';
import RiskAnalyser from '@/components/RiskAnalyser';
import { getAuthenticatedUser } from '../page'; // Reuse auth function

export default async function RiskAnalyserPage() {
  let user;
  try {
    user = await getAuthenticatedUser();
  } catch (error) {
    throw error;
  }
  
  return (
    <>
      <Header userName={user.name} /> 
      <main>
        <RiskAnalyser />
      </main>
    </>
  );
}