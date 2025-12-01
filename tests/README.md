# Tests

Test suite with 49 tests covering all API endpoints and Redis caching.

## Running Tests

```bash
# Parallel (default, ~3-5s)
pytest

# Sequential (debugging)
pytest -n 0

# With coverage
pytest --cov=app

# Specific file/test
pytest tests/test_auth.py
pytest tests/test_redis_caching.py
pytest tests/test_auth.py::TestLogin::test_login_success
```

## Test Structure

```
tests/
├── conftest.py             # Fixtures and configuration
├── test_auth.py            # Authentication (9 tests)
├── test_sensors.py         # Sensor management (15 tests)
├── test_records.py         # Sensor records (14 tests)
└── test_redis_caching.py   # Redis caching (5 tests)
```

## Configuration

- **Parallel execution**: `-n 4` workers (pytest-xdist)
- **Database**: In-memory SQLite per worker
- **Isolation**: Each test gets fresh database
- **Asyncio**: Full async/await support

## Key Fixtures

- `client` - HTTP test client
- `test_user` / `test_user2` - Pre-created users with tokens
- `auth_headers` - Authorization headers
- `test_sensor` - Pre-created sensor
- `test_db_session` - Database session

## Performance

| Mode | Workers | Time | Tests |
|------|---------|------|-------|
| Sequential | 1 | ~10s | 49 |
| Parallel | 4 | ~4-6s | 49 |


