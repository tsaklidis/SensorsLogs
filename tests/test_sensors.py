"""
Tests for sensor management endpoints.
"""
import pytest
from httpx import AsyncClient


class TestCreateSensor:
    """Tests for creating sensors."""

    async def test_create_sensor_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful sensor creation."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "Temperature Sensor", "location": "Living Room"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Temperature Sensor"
        assert data["location"] == "Living Room"
        assert "id" in data
        assert "owner_id" in data
        assert data["owner_id"] is not None

    async def test_create_sensor_without_location(self, client: AsyncClient, auth_headers: dict):
        """Test creating sensor without location."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "Humidity Sensor"},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Humidity Sensor"
        assert data["location"] is None

    async def test_create_sensor_without_auth(self, client: AsyncClient):
        """Test creating sensor without authentication."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "Test Sensor"}
        )

        assert response.status_code == 401

    async def test_create_sensor_invalid_token(self, client: AsyncClient):
        """Test creating sensor with invalid token."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "Test Sensor"},
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_create_sensor_empty_name(self, client: AsyncClient, auth_headers: dict):
        """Test creating sensor with empty name."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": ""},
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_create_sensor_name_too_long(self, client: AsyncClient, auth_headers: dict):
        """Test creating sensor with name too long."""
        response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "x" * 300},
            headers=auth_headers
        )

        assert response.status_code == 422


class TestListSensors:
    """Tests for listing sensors."""

    async def test_list_sensors_empty(self, client: AsyncClient, auth_headers: dict):
        """Test listing sensors when user has none."""
        response = await client.get(
            "/api/v1.0/sensors",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_sensors_with_data(self, client: AsyncClient, auth_headers: dict):
        """Test listing sensors when user has sensors."""
        # Create multiple sensors
        await client.post(
            "/api/v1.0/sensors",
            json={"name": "Sensor 1", "location": "Location 1"},
            headers=auth_headers
        )
        await client.post(
            "/api/v1.0/sensors",
            json={"name": "Sensor 2", "location": "Location 2"},
            headers=auth_headers
        )

        response = await client.get(
            "/api/v1.0/sensors",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in sensor for sensor in data)
        assert all("name" in sensor for sensor in data)

    async def test_list_sensors_only_own(
        self,
        client: AsyncClient,
        auth_headers: dict,
        auth_headers2: dict
    ):
        """Test that users only see their own sensors."""
        # User 1 creates sensor
        await client.post(
            "/api/v1.0/sensors",
            json={"name": "User 1 Sensor"},
            headers=auth_headers
        )

        # User 2 creates sensor
        await client.post(
            "/api/v1.0/sensors",
            json={"name": "User 2 Sensor"},
            headers=auth_headers2
        )

        # User 1 lists sensors
        response1 = await client.get(
            "/api/v1.0/sensors",
            headers=auth_headers
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1) == 1
        assert data1[0]["name"] == "User 1 Sensor"

        # User 2 lists sensors
        response2 = await client.get(
            "/api/v1.0/sensors",
            headers=auth_headers2
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]["name"] == "User 2 Sensor"

    async def test_list_sensors_without_auth(self, client: AsyncClient):
        """Test listing sensors without authentication."""
        response = await client.get("/api/v1.0/sensors")

        assert response.status_code == 401


class TestDeleteSensor:
    """Tests for deleting sensors."""

    async def test_delete_sensor_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test successful sensor deletion."""
        response = await client.delete(
            f"/api/v1.0/sensors/{test_sensor['id']}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify sensor is deleted
        list_response = await client.get(
            "/api/v1.0/sensors",
            headers=auth_headers
        )
        sensors = list_response.json()
        assert test_sensor['id'] not in [s['id'] for s in sensors]

    async def test_delete_sensor_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test deleting nonexistent sensor."""
        response = await client.delete(
            "/api/v1.0/sensors/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_delete_sensor_not_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        auth_headers2: dict
    ):
        """Test deleting sensor owned by another user."""
        # User 1 creates sensor
        create_response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "User 1 Sensor"},
            headers=auth_headers
        )
        sensor_id = create_response.json()["id"]

        # User 2 tries to delete it
        response = await client.delete(
            f"/api/v1.0/sensors/{sensor_id}",
            headers=auth_headers2
        )

        assert response.status_code == 404

    async def test_delete_sensor_without_auth(self, client: AsyncClient, test_sensor: dict):
        """Test deleting sensor without authentication."""
        response = await client.delete(
            f"/api/v1.0/sensors/{test_sensor['id']}"
        )

        assert response.status_code == 401

    async def test_delete_sensor_invalid_token(self, client: AsyncClient, test_sensor: dict):
        """Test deleting sensor with invalid token."""
        response = await client.delete(
            f"/api/v1.0/sensors/{test_sensor['id']}",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

