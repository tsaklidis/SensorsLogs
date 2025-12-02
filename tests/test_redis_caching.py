"""
Tests for Redis caching functionality.
"""
import pytest
from app.databases.redis import (
    cache_sensor_record,
    get_cached_sensor_record,
    cache_sensor_records_list,
    get_cached_sensor_records_list,
    invalidate_sensor_cache
)


class TestRedisCaching:
    """Tests for Redis caching operations."""

    async def test_cache_and_retrieve_sensor_record(self):
        """Test caching and retrieving a single sensor record."""
        sensor_id = 999
        value = 23.5
        timestamp = "2025-12-01T10:00:00"

        # Cache the record
        result = await cache_sensor_record(sensor_id, value, timestamp)
        assert result is True

        # Retrieve the cached record
        cached = await get_cached_sensor_record(sensor_id)
        assert cached is not None
        assert cached["value"] == value
        assert cached["created_at"] == timestamp

        # Cleanup
        await invalidate_sensor_cache(sensor_id)

    async def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        sensor_id = 888

        # Ensure cache is empty
        await invalidate_sensor_cache(sensor_id)

        # Try to get non-existent cached record
        cached = await get_cached_sensor_record(sensor_id)
        assert cached is None


    async def test_cache_invalidation(self):
        """Test cache invalidation clears all sensor data."""
        sensor_id = 666

        # Cache both record and list
        await cache_sensor_record(sensor_id, 23.5, "2025-12-01T10:00:00")
        await cache_sensor_records_list(sensor_id, [
            {"value": 23.5, "created_at": "2025-12-01T10:00:00"}
        ])

        # Verify data is cached
        assert await get_cached_sensor_record(sensor_id) is not None
        assert await get_cached_sensor_records_list(sensor_id) is not None

        # Invalidate cache
        result = await invalidate_sensor_cache(sensor_id)
        assert result is True

        # Verify cache is empty
        assert await get_cached_sensor_record(sensor_id) is None
        assert await get_cached_sensor_records_list(sensor_id) is None

    async def test_multiple_sensors_isolated(self):
        """Test that different sensors have isolated caches."""
        sensor_id_1 = 555
        sensor_id_2 = 444

        # Cache different values for different sensors
        await cache_sensor_record(sensor_id_1, 10.0, "2025-12-01T10:00:00")
        await cache_sensor_record(sensor_id_2, 20.0, "2025-12-01T10:00:00")

        # Retrieve and verify isolation
        cached_1 = await get_cached_sensor_record(sensor_id_1)
        cached_2 = await get_cached_sensor_record(sensor_id_2)

        assert cached_1["value"] == 10.0
        assert cached_2["value"] == 20.0

        # Invalidate one sensor
        await invalidate_sensor_cache(sensor_id_1)

        # Verify only one is cleared
        assert await get_cached_sensor_record(sensor_id_1) is None
        assert await get_cached_sensor_record(sensor_id_2) is not None

        # Cleanup
        await invalidate_sensor_cache(sensor_id_2)



