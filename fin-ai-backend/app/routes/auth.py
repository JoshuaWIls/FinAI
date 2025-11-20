#/Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-backend/app/routes/auth.py
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from app.models import UserLogin, UserRegister, UserOut
from app.services.mongo_service import (
    register_user as register_user_db, 
    authenticate_user,
    get_user_by_id_str,
    get_db_user
)
from app.services.auth_service import (
    create_access_token,
    get_current_user,
    create_auth_cookie,
    clear_auth_cookie
)
import traceback

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify auth router is working"""
    return {
        "status": "ok",
        "message": "Auth router is working properly"
    }


@router.post("/register")
async def register_user(user_data: UserRegister): 
    """Registers a new user."""
    try:
        print(f"📝 Registration attempt for: {user_data.email}")
        
        # Check if user already exists
        existing_user = await get_db_user(user_data.email)
        if existing_user:
            print(f"⚠️  User already exists: {user_data.email}")
            raise HTTPException(
                status_code=409, 
                detail="User with this email already exists"
            )

        # Register the user
        user = await register_user_db(user_data)
        
        if not user:
            print(f"❌ Failed to create user: {user_data.email}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create user"
            )
        
        print(f"✅ User registered successfully: {user['email']}")
        
        return JSONResponse(
            content={
                "message": "User registered successfully. Please log in.",
                "userId": str(user["_id"])
            },
            status_code=201
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login_for_access_token(form_data: UserLogin):
    """Authenticates user and sets auth cookie."""
    try:
        print(f"🔐 Login attempt for: {form_data.email}")
        
        user = await authenticate_user(form_data.email, form_data.password)
        
        if not user:
            print(f"⚠️  Invalid credentials for: {form_data.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
            )

        access_token = create_access_token(data={"sub": str(user["_id"])})

        response = JSONResponse(
            content={
                "message": "Login successful",
                "user": {
                    "id": str(user["_id"]),
                    "email": user["email"],
                    "name": user.get("name", ""),
                }
            },
            status_code=200
        )
        
        cookie_string = create_auth_cookie(access_token)
        response.headers["Set-Cookie"] = cookie_string
        
        print(f"✅ User logged in: {user['email']}")
        print(f"🍪 Cookie set: {cookie_string[:50]}...")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout_user():
    """Clears the authentication cookie."""
    try:
        response = JSONResponse(
            content={"message": "Logged out successfully"},
            status_code=200
        )
        response.headers["Set-Cookie"] = clear_auth_cookie()
        
        print("👋 User logged out")
        
        return response
    except Exception as e:
        print(f"❌ Logout error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Logout failed"
        )


@router.get("/user", response_model=UserOut)
async def read_user_me(request: Request, current_user: dict = Depends(get_current_user)):
    """Returns the currently authenticated user's details."""
    try:
        user_data = await get_user_by_id_str(str(current_user["_id"]))
        
        if not user_data:
            raise HTTPException(
                status_code=404, 
                detail="User not found"
            )
        
        return UserOut(
            id=str(user_data["_id"]),
            email=user_data["email"],
            name=user_data.get("name", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get user error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch user data"
        )