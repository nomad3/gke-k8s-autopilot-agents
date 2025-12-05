#!/bin/sh
set -e

echo "================================"
echo "Backend Database Initialization"
echo "================================"

# Extract connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp/IqIw1xI="
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DB="dental_erp_dev"

echo "Installing PostgreSQL client..."
apk add --no-cache postgresql-client

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is ready!"

echo "Checking if database '$POSTGRES_DB' exists..."
DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

if [ "$DB_EXISTS" = "1" ]; then
  echo "Database '$POSTGRES_DB' already exists."
else
  echo "Creating database '$POSTGRES_DB'..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE $POSTGRES_DB;"
  echo "Database '$POSTGRES_DB' created successfully!"
fi

echo "Granting privileges..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"

echo "Database initialization complete!"
echo ""
echo "Installing dependencies..."
npm install --include=dev

echo ""
echo "Running database migrations..."
npm run db:migrate

echo ""
echo "Seeding database..."
npm run db:seed

echo ""
echo "================================"
echo "Backend database setup complete!"
echo "================================"
