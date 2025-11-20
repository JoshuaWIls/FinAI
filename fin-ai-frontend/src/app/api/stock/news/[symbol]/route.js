//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/app/api/stock/news/[symbol]/route.js
import { NextResponse } from "next/server";

export async function GET(req, { params }) {
  const { symbol } = params;

  try {
    const response = await fetch(`http://localhost:8000/news/${symbol}`);

    if (!response.ok) {
      return NextResponse.json(
        { message: "Failed to fetch news from backend" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error fetching news data:", error);
    return NextResponse.json(
      { message: "Error fetching news data", error: error.message },
      { status: 500 }
    );
  }
}
