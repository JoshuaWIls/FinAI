# fin-ai-backend/app/routes/chatbot.py
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.services.chatbot_service import (
    generate_chatbot_response, 
    get_investment_recommendations
)
from app.services.mongo_service import get_user_by_id_str
from app.services.auth_service import get_current_user  # ⭐ Import your existing auth

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Message]] = None


class RecommendationRequest(BaseModel):
    pass


# ⭐ UPDATED: Use your existing JWT authentication
async def get_current_user_id(current_user: dict = Depends(get_current_user)):
    """Extract user ID from JWT token (using existing auth system)."""
    user_id = str(current_user["_id"])
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("/query")
async def chat_query(
    chat_request: ChatRequest,
    user_id: str = Depends(get_current_user_id)  # ⭐ Use dependency injection
):
    """
    Handle chatbot queries with personalized responses.
    
    Endpoint: POST /api/chatbot/query
    Body: {
        "message": "User's question",
        "conversation_history": [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
    }
    """
    try:
        # Validate user exists
        user = await get_user_by_id_str(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert conversation history to dict format if provided
        history = None
        if chat_request.conversation_history:
            history = [msg.dict() for msg in chat_request.conversation_history]
        
        # Generate response
        result = await generate_chatbot_response(
            user_id=user_id,
            user_message=chat_request.message,
            conversation_history=history
        )
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["response"])
        
        return {
            "response": result["response"],
            "stock_data": result.get("stock_data"),
            "user_name": result.get("user_name"),
            "timestamp": str(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat_query endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your request"
        )


@router.get("/recommendations")
async def get_recommendations(user_id: str = Depends(get_current_user_id)):
    """
    Get personalized investment recommendations.
    
    Endpoint: GET /api/chatbot/recommendations
    """
    try:
        # Validate user exists
        user = await get_user_by_id_str(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate recommendations
        recommendations = await get_investment_recommendations(user_id)
        
        if not recommendations:
            raise HTTPException(
                status_code=500, 
                detail="Could not generate recommendations"
            )
        
        return {
            "recommendations": recommendations,
            "user_name": user.get("name"),
            "generated_at": str(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_recommendations endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating recommendations"
        )


@router.get("/user-profile")
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's profile information for the chatbot.
    
    Endpoint: GET /api/chatbot/user-profile
    """
    try:
        # Get user data
        user = await get_user_by_id_str(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return relevant profile data (exclude sensitive info like password)
        return {
            "name": user.get("name"),
            "email": user.get("email"),
            "occupation": user.get("occupation"),
            "current_salary": user.get("currentSalary"),
            "date_of_birth": str(user.get("dateOfBirth", ""))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_user_profile endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching user profile"
        )