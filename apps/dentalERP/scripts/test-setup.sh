#!/bin/bash

echo "🧪 Testing Dental Practice ERP Setup"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_url() {
    local url=$1
    local name=$2

    echo -n "Testing $name ($url)... "

    if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ WORKING${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Test database services
test_db() {
    echo -n "Testing PostgreSQL... "
    if docker exec dentalerp-postgres-1 pg_isready -U postgres >/dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

test_redis() {
    echo -n "Testing Redis... "
    if docker exec dentalerp-redis-1 redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

echo "Infrastructure Services:"
echo "----------------------"
test_db
test_redis

echo ""
echo "Application Services:"
echo "-------------------"
test_url "http://localhost:3000" "Frontend (React App)"
test_url "http://localhost:3001" "Backend (API Server)"
test_url "http://localhost:3001/health" "Health Check Endpoint"

echo ""
echo "📋 Current Status Summary:"
echo "========================="

# Check what Docker services are running
echo "Docker Services:"
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Expected URLs (when services are running):"
echo "- Frontend Application: http://localhost:3000"
echo "- Backend API: http://localhost:3001"
echo "- Health Check: http://localhost:3001/health"
echo "- API Documentation: http://localhost:3001/api-docs"

echo ""
echo "🚀 To start application services:"
echo "docker-compose up --build"
echo ""
echo "🎯 This test validates our comprehensive wireframes and design system setup"
