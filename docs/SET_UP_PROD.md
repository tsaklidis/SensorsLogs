# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Sensors API in a production environment.

## 1. Application Setup

### Clone Repository

```bash
cd /opt
sudo git clone <repository-url> sensors
sudo chown -R $USER:$USER sensors
cd sensors
```

### Generate Secrets

Generate secure random values for your environment variables:

```bash
# JWT Secret (minimum 32 characters)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# API Token for health checks
python3 -c "import secrets; print('APP_API_TOKEN=' + secrets.token_urlsafe(32))"

# Admin Panel URL (randomized path)
python3 -c "import secrets; print('ADMIN_URL=/admin-' + secrets.token_urlsafe(16))"

# PostgreSQL Password
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(24))"

# Redis Password
python3 -c "import secrets; print('REDIS_CACHE_PASSWORD=' + secrets.token_urlsafe(24))"
```

## 3. Environment Configuration

Create your production `.env` file:

```bash
cp .env.example .env
nano .env
```

### Required Environment Variables

```bash
# API Configuration
BASE_URL=https://yourdomain.com
APP_API_TOKEN=<generated_token_from_step_2>

# Admin Panel (use generated random path)
ADMIN_URL=/admin-<random_string>

# JWT Configuration (CRITICAL - must be set!)
JWT_SECRET_KEY=<generated_secret_from_step_2>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sensors_db
POSTGRES_USER=sensorsuser
POSTGRES_PASSWORD=<generated_password_from_step_2>

# Redis Configuration
REDIS_CACHE_HOST=redis-cache
REDIS_CACHE_PORT=6379
REDIS_CACHE_USE_SSL=0
REDIS_CACHE_PASSWORD=<generated_password_from_step_2>
REDIS_CACHE_DB=0

# Logging (INFO for production)
LOG_LEVEL=20
SQL_LOG_LEVEL=30
```

### Security Checklist

Before deploying, verify:

- [ ] `JWT_SECRET_KEY` is set to a secure random value (32+ characters)
- [ ] `POSTGRES_PASSWORD` is strong (24+ characters, random)
- [ ] `REDIS_CACHE_PASSWORD` is strong (24+ characters, random)
- [ ] `ADMIN_URL` is set to a random, non-guessable path
- [ ] `APP_API_TOKEN` is set to a secure random value
- [ ] `BASE_URL` matches your production domain

## 4. Database Initialization

### Start Database Services

```bash
docker-compose up -d postgres redis-cache
```

Wait for databases to be ready (about 30 seconds):

```bash
docker-compose logs -f postgres
# Wait for "database system is ready to accept connections"
# Press Ctrl+C to exit logs
```

### Run Migrations

```bash
# Apply database schema
docker-compose run --rm sensors_app alembic upgrade head
```

## 5. Create Admin User

Create your first administrator account using SQL queries.

### Connect to PostgreSQL

```bash
docker-compose exec postgres psql -U sensorsuser -d sensors_db
```

### Create Admin User with SQL

```sql
-- Generate bcrypt hash for password "ChangeThisPassword123!"
-- Note: Replace the hash below with your own generated hash
-- You can generate one using: python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('YourPassword'))"

INSERT INTO users (
    username, 
    email, 
    hashed_password, 
    full_name, 
    is_active, 
    is_admin,
    created_at,
    failed_login_attempts
) VALUES (
    'admin',
    'admin@yourdomain.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYL3A1Fqeqy',  -- Hash for "ChangeThisPassword123!"
    'System Administrator',
    true,
    true,
    NOW(),
    0
);

-- Verify user was created
SELECT id, username, email, full_name, is_active, is_admin, created_at 
FROM users 
WHERE username = 'admin';

-- Exit psql
\q
```

### Alternative: Generate Password Hash

If you want to use a different password, generate the bcrypt hash first:

```bash
# Generate bcrypt hash for your custom password
docker-compose run --rm sensors_app python3 -c "
from passlib.hash import bcrypt
password = 'YourSecurePassword123!'
hashed = bcrypt.hash(password)
print(f'Hashed password: {hashed}')
"
```

Then use the generated hash in the SQL INSERT statement above.

**Important**: Change the default password immediately after first login through the admin panel.

## 6. Health Checks

Test that all services are running:

```bash
# Get your APP_API_TOKEN from .env
API_TOKEN=$(grep APP_API_TOKEN .env | cut -d '=' -f2)

# Check PostgreSQL
curl -H "api-token: $API_TOKEN" https://yourdomain.com/health/psql

# Check Redis
curl -H "api-token: $API_TOKEN" https://yourdomain.com/health/redis

# Check Redis read/write
curl -H "api-token: $API_TOKEN" https://yourdomain.com/health/redis_rw
```

All should return `{"healthy": true}`.

## Support

For issues or questions:

- Review logs first
- Check [API documentation](API.md)
- Review application code in `app/`
- Contact system administrator

---

**Author**: Stefanos I. Tsaklidis  
**Website**: [tsaklidis.gr](https://tsaklidis.gr)

