import motor.motor_asyncio
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")

async def test_connection():
    try:
        print(f"Testing connection to: {MONGO_URI}")
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )
        
        # Test the connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List databases
        dbs = await client.list_database_names()
        print(f"📚 Available databases: {dbs}")
        
        client.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())