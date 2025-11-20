//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/api/stock/news/route.js
import { NextResponse } from "next/server";

export async function GET() {
  const FINNHUB_API_KEY = process.env.FINNHUB_API_KEY;

  if (!FINNHUB_API_KEY) {
    return NextResponse.json({ message: "API key is missing" }, { status: 500 });
  }

  try {
    const response = await fetch(
      `https://finnhub.io/api/v1/news?category=general&token=${FINNHUB_API_KEY}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Finnhub API Error:", errorData);
      return NextResponse.json({ message: "Failed to fetch news from Finnhub" }, { status: response.status });
    }

    const newsData = await response.json();
    return NextResponse.json(newsData, { status: 200 });
  } catch (error) {
    console.error("Error fetching general news:", error);
    return NextResponse.json({ message: "Internal Server Error", error: error.message }, { status: 500 });
  }
}
