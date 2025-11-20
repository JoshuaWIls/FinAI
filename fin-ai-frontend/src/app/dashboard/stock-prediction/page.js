//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/dashboard/stock-prediction/page.js
import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import Header from '@/components/Header';
import StockPrediction from '@/components/StockPrediction';
import { getAuthenticatedUser } from '../page'; 

export default async function StockPredictionPage() {
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
        <StockPrediction />
      </main>
    </>
  );
}