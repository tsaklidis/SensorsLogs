# Sensors API

A production-ready FastAPI application for managing IoT sensor data with secure JWT authentication and multi-tenant architecture.

## Overview

This system provides a RESTful API for IoT devices to register sensors and submit telemetry data. Built with performance and security in mind, it features Redis caching for low-latency reads, PostgreSQL for durable storage, and comprehensive authentication mechanisms.

## Key Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Multi-Tenant Architecture**: Complete user isolation with ownership-based permissions
- **High-Performance Caching**: Redis caching layer with automatic database persistence
- **Admin Dashboard**: Web-based interface for user and sensor management
- **Rate Limiting**: Configurable per-endpoint rate limits to prevent abuse
- **Database Migrations**: Version-controlled schema changes with Alembic
- **Comprehensive Testing**: 49 automated tests with parallel execution support

## Technology Stack

**Backend Framework**
- FastAPI with async/await support
- Python 3.12+
- Uvicorn ASGI server

**Database Layer**
- PostgreSQL 13+ for persistent storage
- SQLModel for type-safe ORM operations
- Alembic for database migrations

**Caching & Performance**
- Redis for sensor data caching
- Background task processing for write operations
- Optimized query patterns with automatic cache invalidation

**Security**
- PyJWT for token generation and validation
- Bcrypt password hashing (cost factor 12)
- Rate limiting with sliding window algorithm
- Security headers and CORS configuration

## Getting Started

### Development Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd sensors
pip install -r requirements.txt
```

Configure your environment:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Start the development server:

```bash
# With Docker
docker-compose up -d

# Manual
alembic upgrade head
uvicorn app.main:app --reload
```

Access the API documentation at `http://localhost:8000/docs`

### User Management

This system does not support public registration. Users must be created by administrators through the admin panel.

Access the admin panel at: `http://localhost:8000/<ADMIN_URL>`

The `ADMIN_URL` is configured via environment variable for security purposes.


## Project Architecture

```
sensors/
├── app/
│   ├── main.py                    # Application entry point and configuration
│   ├── api/
│   │   ├── base.py                # Base router configuration
│   │   ├── deps.py                # Dependency injection
│   │   └── v1/routers.py          # API v1.0 endpoints
│   ├── core/
│   │   ├── config.py              # Environment settings and validation
│   │   ├── jwt_service.py         # Token generation and validation
│   │   └── rate_limit.py          # Rate limiting implementation
│   ├── databases/
│   │   ├── models.py              # SQLModel database models
│   │   ├── crud.py                # Database operations
│   │   ├── manager.py             # Connection management
│   │   └── redis.py               # Redis cache operations
│   ├── admin/
│   │   └── admin.py               # Admin panel interface
│   ├── errors/
│   │   └── api_errors.py          # Custom exception handlers
│   └── utils/
│       └── generators.py          # Utility functions
├── alembic/                       # Database migration scripts
├── tests/                         # Test suite (49 tests)
└── docs/                          # Additional documentation
```

## Security

This application implements multiple layers of security controls:

**Authentication**
- JWT tokens with configurable expiration periods
- Bcrypt password hashing with cost factor 12
- Secure token generation requiring 32+ character secrets
- Protection against timing attacks during authentication

**Rate Limiting**
- Configurable per-endpoint rate limits
- Login attempts limited to 5 per minute
- Account lockout after failed attempts

**Infrastructure Security**
- SQL injection prevention via ORM
- Input validation with Pydantic schemas
- CORS configuration for cross-origin protection
- Security headers (XSS, clickjacking, MIME sniffing protection)
- Admin panel access via randomized URL

For production deployment, refer to the [production setup guide](docs/SET_UP_PROD.md) for hardening procedures.

## Development

### Running Tests

The test suite includes 49 tests covering authentication, sensor management, data recording, and caching:

```bash
# Run all tests (parallel execution)
pytest

# Run with coverage report
pytest --cov=app

# Sequential execution for debugging
pytest -n 0

# Run specific test file
pytest tests/test_auth.py
```

### Database Migrations

Create and apply schema changes:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Documentation

- **[API Reference](docs/API.md)** - Complete endpoint documentation with examples
- **[Production Setup](docs/SET_UP_PROD.md)** - Step-by-step production deployment guide

## Configuration

All configuration is managed through environment variables. See `.env.example` for all available options.

Critical settings:
- `JWT_SECRET_KEY` - Must be 32+ characters (required)
- `POSTGRES_PASSWORD` - Strong database password
- `REDIS_CACHE_PASSWORD` - Redis authentication
- `ADMIN_URL` - Randomized admin panel path
- `APP_API_TOKEN` - Health check endpoint authentication


## License

[Add your license here]

## Author

**Stefanos I. Tsaklidis**  
Website: [tsaklidis.gr](https://tsaklidis.gr)

---

For API usage instructions, see [API.md](docs/API.md)  
For production deployment, see [SET_UP_PROD.md](docs/SET_UP_PROD.md)
