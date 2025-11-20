#/Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-backend/app/services/auth_service.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status, Request
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hashes a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_auth_cookie(token: str) -> str:
    """Creates the Set-Cookie header string."""
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return f"authToken={token}; HttpOnly; Path=/; Max-Age={max_age}; SameSite=Lax"


def clear_auth_cookie() -> str:
    """Creates a Set-Cookie header to clear the cookie."""
    return "authToken=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"


async def get_current_user(request: Request) -> dict:
    """
    Decodes the token from the cookie and fetches the user from the database.
    """
    from app.services.mongo_service import get_user_by_id_str
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    token = request.cookies.get("authToken")
    
    if token is None:
        print("⚠️  No auth token found in cookies")
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            print("⚠️  No user ID in token payload")
            raise credentials_exception
            
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise credentials_exception

    user = await get_user_by_id_str(user_id)
    
    if user is None:
        print(f"⚠️  User not found for ID: {user_id}")
        raise credentials_exception
        
    return user