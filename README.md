# Sensors API

FastAPI application for managing IoT sensor data with JWT authentication and multi-user support.

## Features

- JWT-based authentication (access & refresh tokens)
- Admin-only user creation (no public registration)
- Multi-user system with sensor ownership
- Sensor and data logging management
- Redis caching for fast sensor reads (with DB persistence)
- Rate limiting (30 req/min)
- PostgreSQL with async SQLModel
- Alembic migrations
- Admin panel for user management

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 13+ with SQLModel
- **Cache**: Redis (for sensor data caching)
- **Auth**: PyJWT with bcrypt password hashing
- **Migrations**: Alembic
- **Python**: 3.12+

## Quick Start

### Docker (Recommended)

```bash
docker-compose up -d
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and JWT secret

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Access API docs at http://localhost:8000/docs

## User Management

Users are created and managed by administrators through the web-based admin panel.

### Access Admin Panel

Navigate to the admin panel URL (configured via `ADMIN_URL` environment variable):

```
http://localhost:8000/<ADMIN_URL>
```

From the admin panel you can:
- Create new users
- View all users
- Activate/deactivate users
- Manage sensors and records

### User Login (API)

```bash
curl -X POST "http://localhost:8000/api/v1.0/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

## Project Structure

```
sensors/
├── app/
│   ├── main.py              # Application entry
│   ├── api/v1/routers.py    # API endpoints
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   └── jwt_service.py   # JWT operations
│   ├── databases/
│   │   ├── models.py        # SQLModel models
│   │   ├── crud.py          # Database operations
│   │   └── serializers.py   # Pydantic schemas
│   └── admin/admin.py       # Admin panel
├── alembic/                 # Migrations
├── tests/                   # Test suite
└── docker-compose.yml       # Docker setup
```

## Configuration

Key environment variables:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=sensors_db
POSTGRES_USER=sensorsuser
POSTGRES_PASSWORD=<strong-password>

# JWT
JWT_SECRET_KEY=<32-byte-secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (required for caching)
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6379
```

## Security

- No public user registration
- JWT tokens with configurable expiration
- Bcrypt password hashing (cost factor 12)
- Rate limiting per IP
- SQL injection protection via ORM
- Input validation with Pydantic

### Production Checklist

- Use HTTPS/TLS
- Set strong `JWT_SECRET_KEY` (32+ bytes)
- Configure proper CORS origins
- Enable monitoring and logging
- Regular database backups
- Use secrets management service

## Development

### Tests

```bash
# Run all tests (parallel)
pytest

# With coverage
pytest --cov=app

# Sequential (for debugging)
pytest -n 0
```

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Documentation

- **[API Reference](docs/API.md)** - Complete endpoint documentation

## Author

Stefanos I. Tsaklidis - https://tsaklidis.gr

