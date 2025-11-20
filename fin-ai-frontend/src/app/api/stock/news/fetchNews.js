//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/api/stock/news/fetchNews.js
export async function fetchStockNews(symbol) {
  try {
    const res = await fetch(`/api/stock/news/${symbol}`);
    if (!res.ok) {
      throw new Error("Failed to fetch news");
    }
    return await res.json();
  } catch (error) {
    console.error("Error fetching stock news:", error);
    return [];
  }
}
