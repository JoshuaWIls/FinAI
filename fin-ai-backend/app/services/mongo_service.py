#/Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-backend/app/services/mongo_service.py
import motor.motor_asyncio
from passlib.context import CryptContext
from app.models import UserRegister
from bson import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime, date

# Load environment variables from .env
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "Financial-AI-Authentication")

if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable is not set!")

print(f"🔗 Connecting to MongoDB: {DB_NAME}")

# Single client instance with proper pooling
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000,
    retryWrites=True,
    maxPoolSize=10,
    minPoolSize=1
)

db = client[DB_NAME]
users_collection = db["users"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_db_user(email: str):
    """Retrieve a user by email."""
    try:
        print(f"🔍 Searching for user: {email}")
        user = await users_collection.find_one({"email": email})
        if user:
            print(f"✅ User found: {email}")
        else:
            print(f"⚠️  User not found: {email}")
        return user
    except Exception as e:
        print(f"❌ Error getting user by email: {e}")
        import traceback
        traceback.print_exc()
        return None


async def register_user(user_data: UserRegister):
    """Register a new user with all form fields."""
    try:
        print(f"🔐 Hashing password for: {user_data.email}")
        hashed_password = pwd_context.hash(user_data.password)
        
        # Convert date to datetime if needed
        dob = user_data.dateOfBirth
        if isinstance(dob, date) and not isinstance(dob, datetime):
            dob = datetime.combine(dob, datetime.min.time())
        
        # Create the user dictionary
        user_dict = {
            "name": user_data.name,
            "email": user_data.email,
            "dateOfBirth": dob,
            "occupation": user_data.occupation,
            "currentSalary": user_data.currentSalary,
            "hashed_password": hashed_password,
            "created_at": datetime.now()
        }
        
        print(f"💾 Inserting user into database: {user_data.email}")
        print(f"📅 Date of birth type: {type(dob)}")
        
        # Insert the complete user document
        result = await users_collection.insert_one(user_dict)
        
        print(f"✅ User inserted with ID: {result.inserted_id}")
        
        # Find and return the newly created user
        new_user = await users_collection.find_one({"_id": result.inserted_id})
        return new_user
    except Exception as e:
        print(f"❌ Error registering user: {e}")
        import traceback
        traceback.print_exc()
        raise


async def authenticate_user(email: str, password: str):
    """Authenticate user credentials."""
    try:
        print(f"🔍 Looking up user: {email}")
        user = await get_db_user(email)
        
        if not user:
            print(f"⚠️  User not found: {email}")
            return None
            
        print(f"🔐 Verifying password for: {email}")
        
        if not pwd_context.verify(password, user["hashed_password"]):
            print(f"⚠️  Invalid password for: {email}")
            return None
            
        print(f"✅ Authentication successful for: {email}")
        return user
    except Exception as e:
        print(f"❌ Error authenticating user: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_user_by_id_str(user_id: str):
    """Retrieve a user by their ID (string)."""
    try:
        obj_id = ObjectId(user_id)
        user = await users_collection.find_one({"_id": obj_id})
        return user
    except Exception as e:
        print(f"❌ Error getting user by ID: {e}")
        import traceback
        traceback.print_exc()
        return None