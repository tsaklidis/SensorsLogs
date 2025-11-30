"""
Tests for sensor records endpoints.
"""
import pytest
from httpx import AsyncClient


class TestCreateRecord:
    """Tests for creating sensor records."""

    async def test_create_record_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test successful record creation."""
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": test_sensor["id"], "value": 23.5},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["value"] == 23.5
        assert "created_at" in data

    async def test_create_record_multiple(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test creating multiple records."""
        values = [23.5, 24.1, 22.8, 25.0]

        for value in values:
            response = await client.post(
                "/api/v1.0/records",
                json={"sensor_id": test_sensor["id"], "value": value},
                headers=auth_headers
            )
            assert response.status_code == 201

        # Verify all records exist
        records_response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}",
            headers=auth_headers
        )
        records = records_response.json()
        assert len(records) == len(values)

    async def test_create_record_nonexistent_sensor(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test creating record for nonexistent sensor."""
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": 99999, "value": 23.5},
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_create_record_not_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        auth_headers2: dict
    ):
        """Test creating record for sensor owned by another user."""
        # User 1 creates sensor
        sensor_response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "User 1 Sensor"},
            headers=auth_headers
        )
        sensor_id = sensor_response.json()["id"]

        # User 2 tries to add record
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": sensor_id, "value": 23.5},
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_create_record_without_auth(
        self,
        client: AsyncClient,
        test_sensor: dict
    ):
        """Test creating record without authentication."""
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": test_sensor["id"], "value": 23.5}
        )

        assert response.status_code == 401

    async def test_create_record_invalid_value_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test creating record with invalid value type."""
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": test_sensor["id"], "value": "not_a_number"},
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_create_record_negative_value(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test creating record with negative value (should be allowed)."""
        response = await client.post(
            "/api/v1.0/records",
            json={"sensor_id": test_sensor["id"], "value": -10.5},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["value"] == -10.5


class TestListRecords:
    """Tests for listing sensor records."""

    async def test_list_records_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test listing records when sensor has none."""
        response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_records_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test listing records when sensor has data."""
        # Add multiple records
        values = [23.5, 24.1, 22.8]
        for value in values:
            await client.post(
                "/api/v1.0/records",
                json={"sensor_id": test_sensor["id"], "value": value},
                headers=auth_headers
            )

        response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(values)
        assert all("value" in record for record in data)
        assert all("created_at" in record for record in data)

    async def test_list_records_nonexistent_sensor(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing records for nonexistent sensor."""
        response = await client.get(
            "/api/v1.0/records/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_list_records_not_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        auth_headers2: dict
    ):
        """Test listing records for sensor owned by another user."""
        # User 1 creates sensor and adds record
        sensor_response = await client.post(
            "/api/v1.0/sensors",
            json={"name": "User 1 Sensor"},
            headers=auth_headers
        )
        sensor_id = sensor_response.json()["id"]

        await client.post(
            "/api/v1.0/records",
            json={"sensor_id": sensor_id, "value": 23.5},
            headers=auth_headers
        )

        # User 2 tries to list records
        response = await client.get(
            f"/api/v1.0/records/{sensor_id}",
            headers=auth_headers2
        )

        assert response.status_code == 403

    async def test_list_records_without_auth(
        self,
        client: AsyncClient,
        test_sensor: dict
    ):
        """Test listing records without authentication."""
        response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}"
        )

        assert response.status_code == 401

    async def test_list_records_chronological_order(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test that records are returned in chronological order."""
        # Add records with different values
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        for value in values:
            await client.post(
                "/api/v1.0/records",
                json={"sensor_id": test_sensor["id"], "value": value},
                headers=auth_headers
            )

        response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}",
            headers=auth_headers
        )

        records = response.json()
        assert len(records) == len(values)

        # Check that timestamps are in order
        timestamps = [record["created_at"] for record in records]
        assert timestamps == sorted(timestamps)


class TestRecordPermissions:
    """Tests for record permission handling."""

    async def test_sensor_without_owner_accessible(
        self,
        client: AsyncClient,
        test_db_session,
        auth_headers: dict
    ):
        """Test that sensors without owner are accessible to all users."""
        # This would require creating a sensor without owner via direct DB access
        # For now, we skip this test as normal API doesn't allow creating ownerless sensors
        pytest.skip("Sensors are always assigned to creator via API")

    async def test_deleted_sensor_records_inaccessible(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_sensor: dict
    ):
        """Test that records become inaccessible after sensor deletion."""
        # Add a record
        await client.post(
            "/api/v1.0/records",
            json={"sensor_id": test_sensor["id"], "value": 23.5},
            headers=auth_headers
        )

        # Delete sensor
        await client.delete(
            f"/api/v1.0/sensors/{test_sensor['id']}",
            headers=auth_headers
        )

        # Try to access records
        response = await client.get(
            f"/api/v1.0/records/{test_sensor['id']}",
            headers=auth_headers
        )

        assert response.status_code == 404

