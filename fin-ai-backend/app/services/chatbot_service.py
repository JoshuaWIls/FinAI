# fin-ai-backend/app/services/chatbot_service.py
import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
from app.services.mongo_service import get_user_by_id_str

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set!")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')


def get_stock_data(symbol: str):
    """Fetch real-time stock data using yfinance."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "previous_close": info.get('previousClose', 'N/A'),
            "open": info.get('open', 'N/A'),
            "day_high": info.get('dayHigh', 'N/A'),
            "day_low": info.get('dayLow', 'N/A'),
            "volume": info.get('volume', 'N/A'),
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
            "fifty_two_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
            "dividend_yield": info.get('dividendYield', 'N/A'),
        }
    except Exception as e:
        print(f"❌ Error fetching stock data: {e}")
        return None


def calculate_age(date_of_birth):
    """Calculate age from date of birth."""
    try:
        if isinstance(date_of_birth, str):
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        else:
            dob = date_of_birth
            
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception as e:
        print(f"❌ Error calculating age: {e}")
        return None


def create_personalized_context(user_data: dict):
    """Create a personalized context for the chatbot based on user data."""
    try:
        age = calculate_age(user_data.get('dateOfBirth'))
        
        context = f"""
You are a highly personalized Financial AI Assistant specifically helping {user_data.get('name', 'User')}.

USER PROFILE:
- Name: {user_data.get('name', 'User')}
- Age: {age if age else 'Unknown'}
- Occupation: {user_data.get('occupation', 'Not specified')}
- Current Salary: ₹{user_data.get('currentSalary', 'Not specified'):,} per year
- Email: {user_data.get('email', 'Not specified')}

PERSONALIZATION GUIDELINES:
1. Always address the user by their name when appropriate
2. Consider their age for investment recommendations (risk tolerance, time horizon)
3. Tailor advice based on their occupation and salary level
4. Provide investment suggestions aligned with their financial capacity
5. Use their salary context when discussing savings rates, investment amounts, and financial goals

EXPERTISE AREAS:
- Stock market analysis and recommendations
- Personal finance and budgeting advice
- Investment strategies (stocks, mutual funds, ETFs, bonds)
- Risk assessment and portfolio diversification
- Tax-saving investment options (especially Indian tax laws if applicable)
- Retirement planning
- Emergency fund recommendations
- Wealth building strategies

RESPONSE STYLE:
- Be conversational, friendly, and encouraging
- Provide specific, actionable advice
- Use real market data when discussing stocks
- Always consider the user's financial situation in recommendations
- Explain complex financial concepts in simple terms
- Include relevant examples and calculations when helpful

Remember: You're not just an AI, you're {user_data.get('name')}'s personal financial advisor who knows their situation and goals.
"""
        return context
    except Exception as e:
        print(f"❌ Error creating personalized context: {e}")
        return "You are a helpful Financial AI Assistant."


async def generate_chatbot_response(user_id: str, user_message: str, conversation_history: list = None):
    """
    Generate a personalized chatbot response using Gemini API.
    
    Args:
        user_id: MongoDB user ID
        user_message: The user's current message
        conversation_history: List of previous messages for context
    
    Returns:
        dict: Response containing the AI's reply and any relevant stock data
    """
    try:
        # Get user data from MongoDB
        user_data = await get_user_by_id_str(user_id)
        if not user_data:
            return {
                "response": "I couldn't retrieve your user profile. Please ensure you're logged in.",
                "error": True
            }
        
        # Check if user is asking about a specific stock
        stock_data = None
        stock_symbols = extract_stock_symbols(user_message)
        if stock_symbols:
            stock_data = {}
            for symbol in stock_symbols:
                data = get_stock_data(symbol)
                if data:
                    stock_data[symbol] = data
        
        # Create personalized context
        system_context = create_personalized_context(user_data)
        
        # Build the conversation for Gemini
        chat_messages = [system_context]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    chat_messages.append(f"User: {content}")
                else:
                    chat_messages.append(f"Assistant: {content}")
        
        # Add stock data context if available
        if stock_data:
            stock_context = "\n\nREAL-TIME STOCK DATA:\n"
            for symbol, data in stock_data.items():
                stock_context += f"""
{symbol}:
- Current Price: ${data['current_price']}
- Previous Close: ${data['previous_close']}
- Day Range: ${data['day_low']} - ${data['day_high']}
- 52-Week Range: ${data['fifty_two_week_low']} - ${data['fifty_two_week_high']}
- P/E Ratio: {data['pe_ratio']}
- Market Cap: {data['market_cap']}
- Volume: {data['volume']}
"""
            chat_messages.append(stock_context)
        
        # Add current user message
        chat_messages.append(f"User: {user_message}")
        chat_messages.append("Assistant: ")
        
        # Generate response using Gemini
        full_prompt = "\n".join(chat_messages)
        response = model.generate_content(full_prompt)
        
        ai_response = response.text
        
        return {
            "response": ai_response,
            "stock_data": stock_data,
            "user_name": user_data.get('name'),
            "error": False
        }
        
    except Exception as e:
        print(f"❌ Error generating chatbot response: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try again.",
            "error": True
        }


def extract_stock_symbols(message: str):
    """
    Extract potential stock symbols from user message.
    Looks for common patterns like: AAPL, GOOGL, TSLA, etc.
    """
    import re
    
    # Common patterns for stock mentions
    patterns = [
        r'\b([A-Z]{1,5})\b',  # 1-5 uppercase letters
        r'\$([A-Z]{1,5})\b',  # $ followed by symbol
    ]
    
    symbols = set()
    for pattern in patterns:
        matches = re.findall(pattern, message.upper())
        symbols.update(matches)
    
    # Filter out common words that might be matched
    common_words = {'I', 'A', 'AI', 'IN', 'ON', 'AT', 'TO', 'FOR', 'THE', 'IS', 'IT', 'OR', 'AND', 'BUT'}
    symbols = {s for s in symbols if s not in common_words}
    
    # Common stock symbols mentioned in context
    stock_keywords = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'amazon': 'AMZN',
        'tesla': 'TSLA',
        'meta': 'META',
        'facebook': 'META',
        'netflix': 'NFLX',
        'nvidia': 'NVDA',
        'reliance': 'RELIANCE.NS',
        'tcs': 'TCS.NS',
        'infosys': 'INFY.NS',
        'wipro': 'WIPRO.NS',
        'hdfc': 'HDFCBANK.NS',
        'icici': 'ICICIBANK.NS',
    }
    
    message_lower = message.lower()
    for keyword, symbol in stock_keywords.items():
        if keyword in message_lower:
            symbols.add(symbol)
    
    return list(symbols)[:3]  # Limit to 3 stocks per query


async def get_investment_recommendations(user_id: str):
    """Generate personalized investment recommendations based on user profile."""
    try:
        user_data = await get_user_by_id_str(user_id)
        if not user_data:
            return None
        
        age = calculate_age(user_data.get('dateOfBirth'))
        salary = user_data.get('currentSalary', 0)
        
        context = create_personalized_context(user_data)
        
        prompt = f"""{context}

Based on {user_data.get('name')}'s profile (Age: {age}, Salary: ₹{salary:,}), provide:

1. Recommended monthly investment amount (considering 50-30-20 rule)
2. Ideal asset allocation (equity, debt, gold, emergency fund)
3. Top 3 specific investment options suitable for their profile
4. Risk tolerance assessment
5. Short-term and long-term financial goals to consider

Be specific with numbers and reasoning. Format the response clearly with sections.
"""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"❌ Error generating investment recommendations: {e}")
        return None