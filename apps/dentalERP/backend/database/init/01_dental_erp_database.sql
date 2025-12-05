-- Create Dental ERP main database
-- This runs automatically when PostgreSQL container starts

-- Create dental_erp_dev database if it doesn't exist
SELECT 'CREATE DATABASE dental_erp_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dental_erp_dev')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dental_erp_dev TO postgres;
