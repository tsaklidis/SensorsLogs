#!/bin/bash
#
# Setup script for Sensors API
# This script sets up a fresh installation of the Sensors API with all dependencies and database migrations
#

set -e  # Exit on error

echo "======================================"
echo "Sensors API - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 is required"; exit 1; }
echo "✓ Python 3 found"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env file"
        echo "⚠️  IMPORTANT: Edit .env and set your configuration values!"
        echo ""
    else
        echo "❌ Error: .env.example not found"
        exit 1
    fi
else
    echo "✓ .env file exists"
    echo ""
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt || { echo "❌ Failed to install dependencies"; exit 1; }
echo "✓ Dependencies installed"
echo ""

# Check if PostgreSQL is accessible
echo "Checking PostgreSQL connection..."
source .env
export PGPASSWORD=$POSTGRES_PASSWORD

# Try to connect to PostgreSQL
if psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ PostgreSQL is accessible"

    # Check if database exists
    if psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -lqt | cut -d \| -f 1 | grep -qw $POSTGRES_DB; then
        echo "✓ Database '$POSTGRES_DB' exists"
    else
        echo "⚠️  Database '$POSTGRES_DB' does not exist. Creating..."
        psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB;" || { echo "❌ Failed to create database"; exit 1; }
        echo "✓ Database created"
    fi
else
    echo "⚠️  Cannot connect to PostgreSQL"
    echo "    Please ensure PostgreSQL is running and credentials in .env are correct"
    echo "    Host: $POSTGRES_HOST:$POSTGRES_PORT"
    echo "    User: $POSTGRES_USER"
    echo "    Database: $POSTGRES_DB"
    echo ""
    echo "    You can skip this and run migrations manually later with:"
    echo "    alembic upgrade head"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Check if Redis is accessible
echo "Checking Redis connection..."
if redis-cli -h $REDIS_CACHE_HOST -p $REDIS_CACHE_PORT ping > /dev/null 2>&1; then
    echo "✓ Redis is accessible"
else
    echo "⚠️  Cannot connect to Redis"
    echo "    Redis is optional but recommended for rate limiting"
    echo "    Host: $REDIS_CACHE_HOST:$REDIS_CACHE_PORT"
fi
echo ""

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || { echo "❌ Migration failed"; exit 1; }
echo "✓ Migrations completed"
echo ""

# Generate JWT secret if not set
if grep -q "JWT_SECRET_KEY=your-jwt-secret-key-here" .env; then
    echo "⚠️  Generating JWT secret key..."
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/JWT_SECRET_KEY=your-jwt-secret-key-here/JWT_SECRET_KEY=$JWT_SECRET/" .env
    else
        # Linux
        sed -i "s/JWT_SECRET_KEY=your-jwt-secret-key-here/JWT_SECRET_KEY=$JWT_SECRET/" .env
    fi
    echo "✓ JWT secret key generated"
fi
echo ""

# Summary
echo "======================================"
echo "Setup Complete! ✅"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Start the server with: uvicorn app.main:app --reload"
echo "3. Access API docs at: http://localhost:8000/docs"
echo "4. Register a user at: POST /api/v1.0/auth/register"
echo ""
echo "For more information, see:"
echo "- docs/JWT_AUTHENTICATION.md - JWT authentication guide"
echo "- docs/MIGRATIONS.md - Database migration guide"
echo "- README.md - Project overview"
echo ""
echo "Happy coding! 🚀"

