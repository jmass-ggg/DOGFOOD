#!/bin/bash
# Setup script for test database

set -e

echo "Setting up test database for DogFood backend..."

# Database configuration
DB_USER="test"
DB_PASSWORD="test"
DB_NAME="testdb"

# Check if PostgreSQL is running
if ! pg_isready > /dev/null 2>&1; then
    echo "Error: PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Try to connect as current user (common in local PostgreSQL setups)
PSQL_CMD="psql"

# Check if user exists, create if not
if ! $PSQL_CMD -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null | grep -q 1; then
    echo "Creating test user..."
    $PSQL_CMD -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || {
        echo "Failed to create user. You may need to run this with a PostgreSQL superuser."
        echo "Try: sudo -u postgres ./setup_test_db.sh"
        exit 1
    }
else
    echo "Test user already exists."
fi

# Check if database exists, create if not
if ! $PSQL_CMD -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Creating test database..."
    $PSQL_CMD -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || {
        echo "Failed to create database. You may need to run this with a PostgreSQL superuser."
        exit 1
    }
else
    echo "Test database already exists."
fi

# Grant privileges
echo "Granting privileges..."
$PSQL_CMD -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

echo ""
echo "Test database setup complete!"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Connection string: postgresql+psycopg://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
