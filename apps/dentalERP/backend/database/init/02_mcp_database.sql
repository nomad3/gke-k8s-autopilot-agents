-- Create MCP database for MCP Server
-- This runs automatically when PostgreSQL container starts

-- Create mcp database if it doesn't exist
SELECT 'CREATE DATABASE mcp'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mcp')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mcp TO postgres;

