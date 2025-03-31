from config import REDIS_URL
from redis.asyncio import Redis, ConnectionPool

pool = ConnectionPool.from_url(REDIS_URL, decode_responses=True)
redis_client: Redis = Redis(connection_pool=pool)  # Direct instance

async def connect_redis():
    """Initialize connection explicitly"""
    await redis_client.ping()  # Test connection

async def close_redis():
    """Close connection and pool"""
    await redis_client.close()
    await pool.disconnect()