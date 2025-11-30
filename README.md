# Sensors Logs API

A production-ready FastAPI application for managing IoT sensor data with JWT authentication, multi-user support, and real-time monitoring.

## ✨ Features

- 🔐 **JWT Authentication** - Secure token-based auth with access & refresh tokens
- 👥 **Multi-User System** - User management with role-based sensor ownership
- 📊 **Sensor Management** - Track multiple sensors with location metadata
- 📝 **Data Logging** - Store and query sensor measurements with timestamps
- ⚡ **Rate Limiting** - Protection against abuse (30 req/min per IP)
- 🏥 **Health Monitoring** - PostgreSQL and Redis health check endpoints
- 🐳 **Docker Ready** - Full containerization with docker-compose
- 📚 **Interactive Docs** - Auto-generated API docs (Swagger UI & ReDoc)
- 🔄 **Database Migrations** - Version-controlled schema with Alembic
- 👨‍💼 **Admin Panel** - Web UI for user and data management

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Redis 6+ (optional, for rate limiting)
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Automated Setup (Recommended)

```bash
git clone <your-repo-url>
cd sensors
./setup.sh
```

The setup script will:
- Install Python dependencies
- Create `.env` from template
- Set up database and run migrations
- Generate JWT secret key
- Show next steps

#### Option 2: Manual Setup

1. **Clone and install dependencies**
   ```bash
   git clone <your-repo-url>
   cd sensors
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (database, JWT secret, etc.)
   ```

3. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb sensors_db
   
   # Run migrations
   alembic upgrade head
   ```

4. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Option 3: Docker Compose

```bash
docker-compose up -d
```

### Verify Installation

Visit http://localhost:8000/docs to see the interactive API documentation.

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[API Reference](docs/API_GUIDE.md)** | Complete API endpoints and usage examples |
| **[Authentication Guide](docs/USER_GUIDE.md)** | How to get and use JWT tokens |
| **[Developer Guide](docs/MIGRATIONS.md)** | Database migrations and development |

## 🏗️ Architecture

```
sensors/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/
│   │   ├── v1/routers.py   # API v1.0 endpoints
│   │   └── deps.py          # Auth & validation dependencies
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   └── jwt_service.py   # JWT token operations
│   ├── databases/
│   │   ├── models.py        # SQLModel database models
│   │   ├── crud.py          # Database operations
│   │   └── serializers.py   # Pydantic schemas
│   └── admin/
│       └── admin.py         # Admin panel setup
├── alembic/                 # Database migrations
├── docs/                    # Documentation
├── docker-compose.yml       # Docker services
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

Key environment variables (see `.env.example` for all options):

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=sensors_db
POSTGRES_USER=sensorsuser
POSTGRES_PASSWORD=<strong-password>

# JWT Authentication
JWT_SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis (Optional)
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6379
```

## 🔐 Security

- JWT tokens with configurable expiration
- Bcrypt password hashing (cost factor 12)
- Rate limiting (30 requests/minute)
- SQL injection protection (ORM)
- Input validation (Pydantic)
- CORS protection
- Environment-based secrets

**Production Checklist:**
- [ ] Use HTTPS/TLS
- [ ] Set strong `JWT_SECRET_KEY` (32+ bytes)
- [ ] Use secret management service (AWS Secrets Manager, etc.)
- [ ] Configure proper CORS origins
- [ ] Enable monitoring and logging
- [ ] Set up regular database backups

## 💻 Development

### Running Tests

```bash
pytest
pytest --cov=app tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Style

```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
flake8 app/
```

## 🐳 Docker

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## 📊 Database Schema

```sql
-- Users with JWT authentication
user (id, username, email, hashed_password, is_active, created_at, updated_at)

-- Sensors with optional ownership
sensor (id, name, location, owner_id → user.id)

-- Sensor measurements
sensorrecord (id, value, sensor_id → sensor.id, created_at)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

[Your License Here]

## 👤 Author

**Stefanos I. Tsaklidis**  
🌐 https://tsaklidis.gr

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases with Python objects
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [PyJWT](https://pyjwt.readthedocs.io/) - JWT tokens
- [bcrypt](https://github.com/pyca/bcrypt) - Password hashing

---

For detailed usage instructions, see:
- 📘 **[API Reference](docs/API_GUIDE.md)** - How to use the API
- 🔑 **[Authentication Guide](docs/USER_GUIDE.md)** - Getting JWT tokens
- 🛠️ **[Developer Guide](docs/MIGRATIONS.md)** - Development setup

