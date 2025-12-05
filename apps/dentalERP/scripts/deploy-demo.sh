#!/bin/bash
#=============================================================================
# Deploy Demo to GCP VM
# Run this script on the GCP VM at /opt/dental-erp
#=============================================================================

set -euo pipefail

PROJECT_ROOT="/opt/dental-erp"
cd "$PROJECT_ROOT"

info() { echo "[deploy-demo] $1"; }
error() { echo "[deploy-demo] ERROR: $1" >&2; }

info "================================================"
info "DEMO DEPLOYMENT CHECKLIST"
info "================================================"

# 1. Pull latest code
info "[1/7] Pulling latest code from GitHub..."
sudo git pull origin main
info "✓ Code updated"

# 2. Check Docker containers
info "[2/7] Checking Docker containers..."
sudo docker ps --format "table {{.Names}}\t{{.Status}}" | grep dentalerp || {
    error "Docker containers not running. Run: sudo ./deploy.sh"
    exit 1
}
info "✓ Docker containers running"

# 3. Check frontend health
info "[3/7] Checking frontend service..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://dentalerp.agentprovision.com || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    info "✓ Frontend is healthy (HTTP 200)"
elif [ "$FRONTEND_STATUS" = "502" ]; then
    error "Frontend returning 502 Bad Gateway"
    info "  Checking frontend container logs..."
    sudo docker logs --tail 50 dentalerp-frontend-prod-1 || true
    info "  Restarting frontend container..."
    sudo docker restart dentalerp-frontend-prod-1
    sleep 5
    info "  Waiting for container to start..."
    sleep 10
else
    error "Frontend returned HTTP $FRONTEND_STATUS"
fi

# 4. Check MCP Server health
info "[4/7] Checking MCP Server..."
MCP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://mcp.agentprovision.com/health || echo "000")
if [ "$MCP_STATUS" = "200" ]; then
    info "✓ MCP Server is healthy (HTTP 200)"
else
    error "MCP Server returned HTTP $MCP_STATUS"
fi

# 5. Load demo data to Snowflake
info "[5/7] Loading demo data to Snowflake..."
if [ -f "$PROJECT_ROOT/.env" ]; then
    info "  Sourcing environment variables..."
    set -a
    source "$PROJECT_ROOT/.env"
    set +a

    info "  Running data loader..."
    sudo -E python3 "$PROJECT_ROOT/scripts/ingest-netsuite-multi-practice.py" || {
        error "Data loading failed. Check Snowflake credentials in .env"
    }
    info "✓ Demo data loaded"
else
    error ".env file not found. Cannot load Snowflake data."
fi

# 6. Verify dynamic tables
info "[6/7] Verifying Snowflake dynamic tables..."
info "  Run manually: SHOW DYNAMIC TABLES IN SCHEMA silver;"
info "  Run manually: SELECT COUNT(*) FROM gold.daily_financial_summary;"

# 7. Test frontend
info "[7/7] Testing frontend..."
curl -s https://dentalerp.agentprovision.com | head -20 | grep -q "<!DOCTYPE html" && {
    info "✓ Frontend returning HTML"
} || {
    error "Frontend not returning HTML"
}

info "================================================"
info "DEPLOYMENT SUMMARY"
info "================================================"
info "  Frontend: https://dentalerp.agentprovision.com"
info "  MCP Server: https://mcp.agentprovision.com"
info "  Login: admin@practice.com / Admin123!"
info ""
info "NEXT STEPS:"
info "  1. Open frontend in browser"
info "  2. Navigate to Analytics → Financial Dashboard"
info "  3. Verify data for Eastlake, Torrey Pines, ADS"
info "================================================"
