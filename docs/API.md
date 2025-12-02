# API Reference

This guide provides comprehensive documentation for integrating with the Sensors API.

## Base URL

```
http://localhost:8000/api/v1.0
```

Replace `localhost:8000` with your production domain when deploying.

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT access token. Include the token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

**Important**: User registration is disabled. Contact your system administrator to create an account.

---

## Authentication Endpoints

### POST /auth/login

Authenticate with username and password to receive JWT tokens.

**Request Body:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `429 Too Many Requests` - Rate limit exceeded (5 attempts/minute)

---

### POST /auth/refresh

Obtain a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token

---

### GET /users/me

Retrieve information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "created_at": "2025-11-30T10:00:00"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

## Sensor Management

### POST /sensors

Register a new sensor. The sensor is automatically assigned to the authenticated user.

**Request Body:**
```json
{
  "name": "Temperature Sensor",
  "location": "Living Room"
}
```

**Field Requirements:**
- `name` (string, required): 1-255 characters
- `location` (string, optional): Up to 255 characters

**Success Response (201 Created):**
```json
{
  "id": 1,
  "name": "Temperature Sensor",
  "location": "Living Room",
  "owner_id": 1
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded (30 requests/minute)

---

### GET /sensors

List all sensors owned by the authenticated user.

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Temperature Sensor",
    "location": "Living Room",
    "owner_id": 1
  },
  {
    "id": 2,
    "name": "Humidity Sensor",
    "location": "Bedroom",
    "owner_id": 1
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated

---

### DELETE /sensors/{sensor_id}

Delete a sensor. Only the owner can delete their sensors.

**Path Parameters:**
- `sensor_id` (integer): ID of the sensor to delete

**Success Response (204 No Content)**

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `404 Not Found` - Sensor not found or permission denied

---

## Sensor Data Recording

### POST /records

Submit a sensor measurement. The value is immediately cached in Redis for fast retrieval and persisted to PostgreSQL asynchronously.

**Request Body:**
```json
{
  "sensor_id": 1,
  "value": 23.5
}
```

**Field Requirements:**
- `sensor_id` (integer, required): Valid sensor ID owned by the user
- `value` (float, required): Measurement value

**Success Response (201 Created):**
```json
{
  "value": 23.5,
  "created_at": "2025-12-01T10:30:00"
}
```

**Performance Notes:**
- Response time: < 10ms (writes to cache, database write is asynchronous)
- Cache invalidation: Automatic on new records

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not the sensor owner
- `404 Not Found` - Sensor not found
- `429 Too Many Requests` - Rate limit exceeded (30 requests/minute)

---

### GET /records/{sensor_id}

Retrieve all measurements for a sensor. Results are cached for 5 minutes.

**Path Parameters:**
- `sensor_id` (integer): ID of the sensor

**Success Response (200 OK):**
```json
[
  {
    "value": 23.5,
    "created_at": "2025-12-01T10:30:00"
  },
  {
    "value": 24.1,
    "created_at": "2025-12-01T10:35:00"
  }
]
```

Records are returned in chronological order.

**Performance:**
- Cache hit: < 5ms
- Cache miss: ~50ms (queries database and caches result)
- Cache TTL: 5 minutes

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not the sensor owner
- `404 Not Found` - Sensor not found

---

## Integration Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1.0"

# Authenticate
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Register a sensor
sensor = requests.post(
    f"{BASE_URL}/sensors",
    headers=headers,
    json={"name": "Temp Sensor", "location": "Office"}
).json()

sensor_id = sensor["id"]

# Submit a measurement
requests.post(
    f"{BASE_URL}/records",
    headers=headers,
    json={"sensor_id": sensor_id, "value": 23.5}
)

# Retrieve all measurements
records = requests.get(
    f"{BASE_URL}/records/{sensor_id}",
    headers=headers
).json()

print(f"Retrieved {len(records)} measurements")
```

---

### cURL

```bash
# Authenticate and store token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1.0/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}' \
  | jq -r '.access_token')

# Register a sensor
SENSOR_ID=$(curl -s -X POST "http://localhost:8000/api/v1.0/sensors" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Temp Sensor", "location": "Office"}' \
  | jq -r '.id')

# Submit a measurement
curl -X POST "http://localhost:8000/api/v1.0/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sensor_id\": $SENSOR_ID, \"value\": 23.5}"

# Retrieve measurements
curl -X GET "http://localhost:8000/api/v1.0/records/$SENSOR_ID" \
  -H "Authorization: Bearer $TOKEN"
```

---

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1.0';

// Authenticate
const loginRes = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { access_token } = await loginRes.json();

const headers = { 
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};

// Register a sensor
const sensorRes = await fetch(`${BASE_URL}/sensors`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ name: 'Temp Sensor', location: 'Office' })
});
const sensor = await sensorRes.json();

// Submit a measurement
await fetch(`${BASE_URL}/records`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ sensor_id: sensor.id, value: 23.5 })
});

// Retrieve measurements
const recordsRes = await fetch(`${BASE_URL}/records/${sensor.id}`, { headers });
const records = await recordsRes.json();

console.log(`Retrieved ${records.length} measurements`);
```

---

## Error Handling

All error responses follow a consistent JSON format:

```json
{
  "detail": "Error description"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Rate Limiting

Most endpoints enforce rate limits to prevent abuse:

- **Authentication endpoints**: 5 requests/minute
- **Sensor operations**: 30 requests/minute
- **Record operations**: 30 requests/minute
- **Health checks**: 10-30 requests/minute

When rate limits are exceeded, the API returns `429 Too Many Requests`.

---

## Health Check Endpoints

Health check endpoints use a separate authentication mechanism with an API token (not JWT). These are intended for infrastructure monitoring.

**Authentication Header:**
```
api-token: <APP_API_TOKEN>
```

The `APP_API_TOKEN` is configured via environment variable and is different from JWT tokens used for user authentication.

### GET /health/psql

Check PostgreSQL database connectivity.

**Success Response (200 OK):**
```json
{
  "healthy": true
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing API token

---### GET /health/redis

Check Redis connectivity with a ping operation.

**Success Response (200 OK):**
```json
{
  "healthy": true
}
```

Or if unhealthy:
```json
{
  "healthy": false,
  "error": "Connection refused"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing API token
- `429 Too Many Requests` - Rate limit exceeded (30 requests/minute)

---

### GET /health/redis_rw

Check Redis read/write operations.

**Success Response (200 OK):**
```json
{
  "healthy": true
}
```

Or if unhealthy:
```json
{
  "healthy": false,
  "error": "Write operation failed"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing API token
- `429 Too Many Requests` - Rate limit exceeded (10 requests/minute)

---

### GET /health/redis_data

List all key-value pairs in Redis (for debugging purposes).

**Success Response (200 OK):**
```json
{
  "sensor:1:records": "[...]",
  "sensor:2:records": "[...]",
  "health:check": "ok"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing API token

---

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to test API endpoints directly from your browser.
