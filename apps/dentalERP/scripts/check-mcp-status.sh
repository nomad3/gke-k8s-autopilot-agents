#!/bin/bash
# Quick MCP Server Status Checker

echo "🔍 MCP Server Status Check"
echo "=========================="
echo ""

# Check if container is running
echo "1. Container Status:"
docker ps -a | grep mcp-server || echo "Container not found"
echo ""

# Check last 30 log lines
echo "2. Recent Logs (last 30 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs dental-erp_mcp-server-prod_1 --tail 30 2>&1
echo ""

# Check environment variables
echo "3. Key Environment Variables:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec dental-erp_mcp-server-prod_1 env 2>/dev/null | grep -E "MCP|POSTGRES|REDIS|ENVIRONMENT" | sort || echo "Cannot access container"
echo ""

# Test endpoints
echo "4. Endpoint Tests:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "  /health ... "
curl -sf http://localhost:8085/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

echo -n "  /health/detailed ... "
curl -sf http://localhost:8085/health/detailed > /dev/null && echo "✅ OK" || echo "❌ FAIL"
echo ""

# Check database
echo "5. Database Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "  MCP database exists ... "
docker exec dental-erp_postgres_1 psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'mcp'" 2>/dev/null | grep -q 1 && echo "✅ YES" || echo "❌ NO (run: docker exec dental-erp_postgres_1 psql -U postgres -c 'CREATE DATABASE mcp;')"
echo ""

echo "6. Python Processes:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec dental-erp_mcp-server-prod_1 ps aux 2>/dev/null | grep -E "python|uvicorn" || echo "No Python processes found"
echo ""

echo "═══════════════════════════════════════════"
echo "Run this to see full error details:"
echo "  docker logs -f dental-erp_mcp-server-prod_1"
echo ""

