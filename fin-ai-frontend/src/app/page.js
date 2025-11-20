//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/page.js
import AuthForm from '@/components/AuthForm';

export default async function Home({ searchParams }) {
  const params = await searchParams;
  const type = params?.form === 'register' ? 'register' : 'login';
  return <AuthForm type={type} />;
}