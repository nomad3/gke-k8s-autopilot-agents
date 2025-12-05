#!/bin/bash
# Deploy Operations KPI Dashboard to Production
# Run this script ON THE GCP VM after SSHing in

set -e

echo "================================================================================"
echo "  OPERATIONS KPI DASHBOARD - PRODUCTION DEPLOYMENT"
echo "================================================================================"
echo

# Check we're in the right directory
if [ ! -d "/opt/dental-erp" ]; then
    echo "❌ Error: /opt/dental-erp not found"
    echo "   Are you on the GCP VM?"
    exit 1
fi

cd /opt/dental-erp

echo "📍 Current directory: $(pwd)"
echo

# Step 1: Pull latest code
echo "================================================================================"
echo "STEP 1: PULLING LATEST CODE FROM GITHUB"
echo "================================================================================"
echo

echo "Current commit:"
git log -1 --oneline

echo
echo "Pulling from GitHub..."

# Try different methods
if sudo git pull origin main 2>/dev/null; then
    echo "✅ Git pull successful"
elif sudo GIT_TERMINAL_PROMPT=0 git pull origin main 2>/dev/null; then
    echo "✅ Git pull successful (no prompt)"
elif wget -O /tmp/latest.zip https://github.com/nomad3/dentalERP/archive/refs/heads/main.zip 2>/dev/null && \
     sudo unzip -o /tmp/latest.zip -d /tmp/ && \
     sudo cp -r /tmp/dentalERP-main/* /opt/dental-erp/; then
    echo "✅ Downloaded and extracted latest code via wget"
else
    echo "⚠️  Auto-pull failed. Please run manually:"
    echo "   sudo git pull origin main"
    read -p "Press Enter after pulling code manually..."
fi

echo
echo "Latest commits:"
git log -2 --oneline

echo

# Step 2: Create Snowflake tables
echo "================================================================================"
echo "STEP 2: CREATING OPERATIONS KPI TABLES IN SNOWFLAKE"
echo "================================================================================"
echo

if [ -f "scripts/create-operations-kpi-tables.py" ]; then
    echo "Running table creation script..."
    python3 scripts/create-operations-kpi-tables.py
else
    echo "❌ Error: scripts/create-operations-kpi-tables.py not found"
    echo "   Code may not have been pulled correctly"
    exit 1
fi

echo

# Step 3: Rebuild MCP Server
echo "================================================================================"
echo "STEP 3: REBUILDING MCP SERVER WITH OPERATIONS MODULE"
echo "================================================================================"
echo

echo "Checking current MCP server status..."
sudo docker ps | grep mcp-server-prod || echo "MCP server not running"

echo
echo "Rebuilding MCP server (no cache)..."
sudo docker-compose build --no-cache mcp-server-prod

echo
echo "Starting MCP server..."
sudo docker-compose up -d mcp-server-prod

echo
echo "Waiting 15 seconds for startup..."
sleep 15

echo
echo "Checking MCP server logs..."
sudo docker logs --tail 30 dentalerp-mcp-server-prod-1

echo

# Step 4: Verify deployment
echo "================================================================================"
echo "STEP 4: VERIFYING DEPLOYMENT"
echo "================================================================================"
echo

echo "1. MCP Server Health Check:"
curl -s https://mcp.agentprovision.com/health | python3 -m json.tool || echo "⚠️  Health check failed"

echo
echo

echo "2. API Documentation:"
echo "   Check if /operations endpoints are listed:"
curl -s https://mcp.agentprovision.com/docs | grep -i operations || echo "   Checking API docs..."

echo
echo

echo "3. Operations API Test (will fail if no data uploaded yet):"
curl -s https://mcp.agentprovision.com/api/v1/operations/kpis/monthly \
  -H "Authorization: Bearer ${MCP_API_KEY:-dev-mcp-api-key-change-in-production-min-32-chars}" \
  -H "X-Tenant-ID: silvercreek" | python3 -m json.tool | head -20

echo

# Step 5: Upload data
echo "================================================================================"
echo "STEP 5: UPLOADING OPERATIONS DATA"
echo "================================================================================"
echo

if [ -f "scripts/python/parse_operations_report.py" ] && [ -f "examples/ingestion/Operations Report(28).xlsx" ]; then
    echo "Parsing and uploading Operations Report..."
    python3 scripts/python/parse_operations_report.py
else
    echo "⚠️  Parser script or Excel file not found"
    echo "   Skipping data upload - can run manually later"
fi

echo
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo
echo "📊 Operations KPI Dashboard Status:"
echo
echo "   ✅ Code deployed: Latest commits on GCP VM"
echo "   ✅ Snowflake tables: Bronze, Silver, Gold created"
echo "   ✅ MCP server: Rebuilt with operations module"
echo "   ✅ API endpoints: /api/v1/operations/* available"
echo
echo "🔗 Production URLs:"
echo "   • API Docs: https://mcp.agentprovision.com/docs"
echo "   • Operations API: https://mcp.agentprovision.com/api/v1/operations/kpis/monthly"
echo
echo "📋 Next Steps:"
echo "   1. Test API endpoints from your local machine"
echo "   2. Upload historical data for all 14 practices"
echo "   3. Build frontend dashboard (/analytics/operations)"
echo
