#!/bin/bash
set -e

export PGPASSWORD=$POSTGRES_PASSWORD
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" -h "$POSTGRES_HOST" <<-EOSQL
    SELECT 'CREATE DATABASE mcp' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp')\gexec
EOSQL
