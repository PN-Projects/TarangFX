import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg
import redis.asyncio as redis

# Load .env
load_dotenv()

async def check_postgres():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    print(f"Checking Postgres connection to: {db_url.split('@')[1] if '@' in db_url else '...'}") # Hide creds
    try:
        conn = await asyncpg.connect(db_url)
        await conn.close()
        print("✅ Postgres connection successful!")
        return True
    except Exception as e:
        print(f"❌ Postgres connection failed: {e}")
        return False

async def check_redis():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"Checking Redis connection to: {redis_url}")
    try:
        r = redis.from_url(redis_url)
        await r.ping()
        await r.close()
        print("✅ Redis connection successful!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def main():
    print("🔍 Starting Environment Verification...")
    
    postgres_ok = await check_postgres()
    redis_ok = await check_redis()
    
    if postgres_ok and redis_ok:
        print("\n🎉 Environment Verified! You can now run the bot.")
        sys.exit(0)
    else:
        print("\n⚠️ Environment Verification Failed. Please check .env and services.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except ImportError as e:
        print(f"❌ Import Error: {e}. Did you install requirements?")
