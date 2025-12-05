#!/bin/bash
# Quick Snowflake Connection Setup for HKTPGHW-ES87244 account
# This script helps you set up and test your Snowflake connection

set -e

echo "❄️  Snowflake Connection Setup"
echo "================================"
echo ""
echo "Account: HKTPGHW-ES87244 (GCP Singapore)"
echo "User: NOMADSIMON"
echo "Role: ACCOUNTADMIN"
echo ""

# Check if we're in the right directory
if [ ! -f "mcp-server/test-snowflake.py" ]; then
    echo "❌ Error: Must run from dentalERP root directory"
    exit 1
fi

cd mcp-server

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Snowflake Connection (GCP Singapore)
SNOWFLAKE_ACCOUNT=HKTPGHW-ES87244
SNOWFLAKE_USER=NOMADSIMON
SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC

# MCP Server
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars
SECRET_KEY=your-secret-key-for-jwt-min-32-chars-abc123

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created"
else
    echo "ℹ️  .env file already exists. Skipping creation."
    echo "   If you want to recreate it, delete .env and run this script again."
fi

echo ""
echo "🔧 Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Dependencies installed"
echo ""

# Test connection
echo "🧪 Testing Snowflake connection..."
echo ""

python test-snowflake.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Success! Snowflake is connected and ready to use."
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Create Bronze/Silver/Gold schemas:"
    echo "      Log in to https://app.snowflake.com/"
    echo "      Run the SQL commands below"
    echo ""
    echo "   2. SQL to run in Snowflake:"
    cat << 'SQL'
      -- Create database (if not exists)
      CREATE DATABASE IF NOT EXISTS DENTAL_ERP_DW;
      USE DATABASE DENTAL_ERP_DW;

      -- Create data layer schemas
      CREATE SCHEMA IF NOT EXISTS BRONZE;
      CREATE SCHEMA IF NOT EXISTS SILVER;
      CREATE SCHEMA IF NOT EXISTS GOLD;

      -- Create a sample Gold table for testing
      CREATE TABLE IF NOT EXISTS GOLD.monthly_production_kpis (
          practice_name VARCHAR(100),
          month_date DATE,
          year_month VARCHAR(7),
          total_production DECIMAL(18,2),
          total_expenses DECIMAL(18,2),
          net_income DECIMAL(18,2),
          profit_margin_pct DECIMAL(5,2),
          mom_production_growth_pct DECIMAL(5,2),
          PRIMARY KEY (practice_name, month_date)
      );

      -- Insert sample data
      INSERT INTO GOLD.monthly_production_kpis VALUES
      ('downtown', '2024-11-01', '2024-11', 250000, 180000, 70000, 28.0, 5.2),
      ('eastside', '2024-11-01', '2024-11', 189000, 138000, 51000, 27.0, 5.0);
SQL
    echo ""
    echo "   3. Start MCP Server:"
    echo "      cd mcp-server"
    echo "      uvicorn src.main:app --reload --host 0.0.0.0 --port 8085"
    echo ""
    echo "   4. Test API (in another terminal):"
    echo "      curl http://localhost:8085/api/v1/warehouse/status \\"
    echo "        -H 'Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars'"
    echo ""
else
    echo ""
    echo "❌ Connection test failed. Check the errors above."
    echo ""
    echo "💡 Common Issues:"
    echo "   - Wrong password? Update in mcp-server/.env"
    echo "   - Network issues? Check your internet connection"
    echo "   - Account suspended? Check your Snowflake account status"
    echo ""
    echo "📖 For help, see: mcp-server/SNOWFLAKE_SETUP_GUIDE.md"
fi

deactivate
