# API Reference

Complete endpoint documentation for the Sensors API.

Base URL: `http://localhost:8000/api/v1.0`

## Authentication

All endpoints except `/auth/login` and `/auth/refresh` require a valid JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

**Note**: Public user registration is disabled. Contact your administrator for account creation.

### POST /auth/login

Authenticate and receive JWT tokens.

**Request:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` - Invalid credentials

### POST /auth/refresh

Refresh expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` - Invalid or expired refresh token

### GET /users/me

Get current authenticated user information.

**Response (200):**
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

**Errors:**
- `401` - Invalid or missing token

## Sensors

### POST /sensors

Create a new sensor (automatically assigned to authenticated user).

**Request:**
```json
{
  "name": "Temperature Sensor",
  "location": "Living Room"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "Temperature Sensor",
  "location": "Living Room",
  "owner_id": 1
}
```

**Fields:**
- `name` (string, required): 1-255 characters
- `location` (string, optional): Up to 255 characters

**Errors:**
- `401` - Not authenticated
- `422` - Validation error

**Rate Limit:** 30 requests/minute

### GET /sensors

List all sensors owned by authenticated user.

**Response (200):**
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

**Errors:**
- `401` - Not authenticated

### DELETE /sensors/{sensor_id}

Delete a sensor (only owner can delete).

**Response (204):** No content

**Errors:**
- `401` - Not authenticated
- `404` - Sensor not found or permission denied

## Sensor Records

### POST /records

Add a measurement to a sensor.

**Request:**
```json
{
  "sensor_id": 1,
  "value": 23.5
}
```

**Response (201):**
```json
{
  "value": 23.5,
  "created_at": "2025-11-30T10:30:00"
}
```

**Fields:**
- `sensor_id` (integer, required): Valid sensor ID
- `value` (float, required): Measurement value

**Errors:**
- `401` - Not authenticated
- `403` - Not sensor owner
- `404` - Sensor not found

**Rate Limit:** 30 requests/minute

### GET /records/{sensor_id}

Get all records for a sensor.

**Response (200):**
```json
[
  {
    "value": 23.5,
    "created_at": "2025-11-30T10:30:00"
  },
  {
    "value": 24.1,
    "created_at": "2025-11-30T10:35:00"
  }
]
```

Records are returned in chronological order.

**Errors:**
- `401` - Not authenticated
- `403` - Not sensor owner
- `404` - Sensor not found

## Usage Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1.0/auth/login",
    json={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Create sensor
sensor = requests.post(
    "http://localhost:8000/api/v1.0/sensors",
    headers=headers,
    json={"name": "Temp Sensor", "location": "Office"}
).json()

# Add measurement
requests.post(
    "http://localhost:8000/api/v1.0/records",
    headers=headers,
    json={"sensor_id": sensor["id"], "value": 23.5}
)

# Get measurements
records = requests.get(
    f"http://localhost:8000/api/v1.0/records/{sensor['id']}",
    headers=headers
).json()
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST "http://localhost:8000/api/v1.0/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}' \
  | jq -r '.access_token')

# Create sensor
SENSOR_ID=$(curl -X POST "http://localhost:8000/api/v1.0/sensors" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Temp Sensor", "location": "Office"}' \
  | jq -r '.id')

# Add measurement
curl -X POST "http://localhost:8000/api/v1.0/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sensor_id\": $SENSOR_ID, \"value\": 23.5}"

# Get measurements
curl -X GET "http://localhost:8000/api/v1.0/records/$SENSOR_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### JavaScript

```javascript
// Login
const loginRes = await fetch('http://localhost:8000/api/v1.0/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});
const { access_token } = await loginRes.json();

const headers = { 
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};

// Create sensor
const sensorRes = await fetch('http://localhost:8000/api/v1.0/sensors', {
  method: 'POST',
  headers,
  body: JSON.stringify({ name: 'Temp Sensor', location: 'Office' })
});
const sensor = await sensorRes.json();

// Add measurement
await fetch('http://localhost:8000/api/v1.0/records', {
  method: 'POST',
  headers,
  body: JSON.stringify({ sensor_id: sensor.id, value: 23.5 })
});

// Get measurements
const recordsRes = await fetch(
  `http://localhost:8000/api/v1.0/records/${sensor.id}`,
  { headers }
);
const records = await recordsRes.json();
```

## Error Responses

All errors return a JSON response:

```json
{
  "detail": "Error description"
}
```

### Common Status Codes

- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized (invalid/missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded

## Rate Limiting

Endpoints marked with rate limiting allow 30 requests per minute per IP address. Exceeded limits return `429 Too Many Requests`.

## Interactive Documentation

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

