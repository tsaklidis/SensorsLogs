import json
import logging
import redis.asyncio as redis

from app.core.config import settings


logger = logging.getLogger(__name__)

# Redis client instance
_redis_cache = None


def get_redis_client():
    """
    Get or create Redis client instance.
    Lazy initialization to avoid event loop issues.
    """
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = redis.Redis(
            host=settings.REDIS_CACHE_HOST,
            port=settings.REDIS_CACHE_PORT,
            db=settings.REDIS_CACHE_DB,
            decode_responses=True,
            ssl=settings.REDIS_CACHE_USE_SSL,
            password=settings.REDIS_CACHE_PASSWORD,
        )
        logger.info(f"Redis connected to: {settings.REDIS_CACHE_HOST}:{settings.REDIS_CACHE_PORT}")
    return _redis_cache


async def save_to_cache(key: str, value: str, expire: int = 86400):
    """
    Save a value to Redis cache.

    Args:
        key (str): The key under which the value will be stored.
        value (str): The value to store.
        expire (int, optional): Expiration time in seconds. If None, no expiration.
    """
    redis_cache = get_redis_client()
    in_cache = await redis_cache.get(key)
    if in_cache:
        logger.error(f"Collision! Key already exists in cache: {key}")
        return False

    try:
        logger.info(f"Saving to cache: {key}:{value}")
        return await redis_cache.set(name=key, value=value, ex=expire)
    except Exception as e:
        logger.error(f"Failed to save to Redis: {e}")


async def cache_sensor_record(sensor_id: int, value: float, timestamp: str, expire: int = 3600):
    """
    Cache the latest sensor record in Redis.

    Args:
        sensor_id: Sensor ID
        value: Sensor value
        timestamp: ISO format timestamp
        expire: Cache expiration in seconds (default 1 hour)
    """
    try:
        redis_cache = get_redis_client()
        key = f"sensor:{sensor_id}:latest"
        data = f"{value}|{timestamp}"
        await redis_cache.set(key, data, ex=expire)
        logger.info(f"Cached sensor record: {key} = {data}")
        return True
    except Exception as e:
        logger.error(f"Failed to cache sensor record: {e}")
        return False


async def get_cached_sensor_record(sensor_id: int):
    """
    Get cached sensor record from Redis.

    Args:
        sensor_id: Sensor ID

    Returns:
        dict with value and timestamp, or None if not cached
    """
    try:
        redis_cache = get_redis_client()
        key = f"sensor:{sensor_id}:latest"
        data = await redis_cache.get(key)

        if data:
            value_str, timestamp = data.split("|")
            logger.info(f"Cache hit for sensor {sensor_id}")
            return {
                "value": float(value_str),
                "created_at": timestamp
            }

        logger.info(f"Cache miss for sensor {sensor_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to get cached sensor record: {e}")
        return None


async def cache_sensor_records_list(sensor_id: int, records: list, expire: int = 300):
    """
    Cache a list of sensor records.

    Args:
        sensor_id: Sensor ID
        records: List of record dicts
        expire: Cache expiration in seconds (default 5 minutes)
    """
    try:
        redis_cache = get_redis_client()
        key = f"sensor:{sensor_id}:records"

        # Convert records to JSON-serializable format
        serializable_records = []
        for r in records:
            created_at = r["created_at"]
            # Convert datetime to ISO string if it has isoformat method
            if hasattr(created_at, "isoformat"):
                created_at = created_at.isoformat()

            serializable_records.append({
                "value": r["value"],
                "created_at": created_at
            })

        data = json.dumps(serializable_records)
        await redis_cache.set(key, data, ex=expire)
        logger.info(f"Cached {len(records)} records for sensor {sensor_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cache sensor records list: {e}")
        return False


async def get_cached_sensor_records_list(sensor_id: int):
    """
    Get cached list of sensor records.

    Args:
        sensor_id: Sensor ID

    Returns:
        List of records or None if not cached
    """
    try:
        redis_cache = get_redis_client()
        key = f"sensor:{sensor_id}:records"
        data = await redis_cache.get(key)

        if data:
            records = json.loads(data)
            logger.info(f"Cache hit for sensor {sensor_id} records list ({len(records)} records)")
            return records

        logger.info(f"Cache miss for sensor {sensor_id} records list")
        return None
    except Exception as e:
        logger.error(f"Failed to get cached sensor records list: {e}")
        return None


async def invalidate_sensor_cache(sensor_id: int):
    """
    Invalidate all cache entries for a sensor.

    Args:
        sensor_id: Sensor ID
    """
    try:
        redis_cache = get_redis_client()
        keys = [
            f"sensor:{sensor_id}:latest",
            f"sensor:{sensor_id}:records"
        ]
        for key in keys:
            await redis_cache.delete(key)
        logger.info(f"Invalidated cache for sensor {sensor_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to invalidate sensor cache: {e}")
        return False


async def get_from_cache(key):
    try:
        redis_cache = get_redis_client()
        return await redis_cache.get(key)
    except Exception as e:
        logger.error(f"Failed to get from Redis: {e}")
        return None