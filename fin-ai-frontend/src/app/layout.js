import '@/styles/globals.css';
export const metadata = {
  title: 'FinAI - Financial Intelligence', 
  description: 'Authentication and Risk Profiling using AI',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {/* 3. The 'children' prop renders the nested pages/routes */}
        {children} 
      </body>
    </html>
  );
}