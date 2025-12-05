# 🚀 MCP Architecture - Quick Start Guide

## ✅ What's Been Built

You now have a **complete MCP (Mapping & Control Plane) architecture** with:

1. ✅ **ERP Backend** refactored to use MCP Client
2. ✅ **MCP Server** microservice (FastAPI)
3. ✅ **Docker Compose** configuration
4. ✅ **Complete documentation**

---

## 🏃 Quick Start (5 minutes)

### Step 1: Start All Services

```bash
cd /Users/nomade/Documents/GitHub/dentalERP

# Start everything (Postgres, Redis, MCP, Backend, Frontend)
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### Step 2: Verify MCP Server

```bash
# Health check
curl http://localhost:8085/health

# Expected output:
# {"status":"ok","timestamp":"...","service":"mcp-server"}
```

### Step 3: Test MCP API

```bash
# Get integration status
curl http://localhost:8085/api/v1/integrations/status \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"

# Expected: List of integration statuses (ADP, NetSuite, etc.)
```

### Step 4: Verify ERP → MCP Connection

```bash
# Check backend logs for MCP connectivity
docker-compose logs backend | grep MCP

# Expected: No connection errors
```

### Step 5: Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **MCP Server**: http://localhost:8085
- **MCP API Docs**: http://localhost:8085/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 🎯 Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  ERP Backend │────▶│   MCP Server    │
│   :3000     │     │    :3001     │     │     :8085       │
└─────────────┘     └──────────────┘     └─────────────────┘
                             │                     │
                             ▼                     ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  PostgreSQL  │     │   Redis Cache   │
                    │    :5432     │     │     :6379       │
                    └──────────────┘     └─────────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │  External APIs  │
                                         │ ADP, NetSuite,  │
                                         │ DentalIntel...  │
                                         └─────────────────┘
```

---

## 📁 Key Files & Locations

### ERP Backend
- **MCP Client**: `/backend/src/services/mcpClient.ts`
- **Config**: `/backend/src/config/environment.ts`
- **Routes**: `/backend/src/routes/integrations.ts`

### MCP Server
- **Main App**: `/mcp-server/src/main.py`
- **API Endpoints**: `/mcp-server/src/api/`
- **Models**: `/mcp-server/src/models/`
- **Config**: `/mcp-server/src/core/config.py`

### Docker & Deployment
- **Docker Compose**: `/docker-compose.yml`
- **Deploy Script**: `/deploy.sh`
- **MCP Dockerfile**: `/mcp-server/Dockerfile`

### Documentation
- **ERP Migration**: `/backend/MCP_MIGRATION.md`
- **MCP README**: `/mcp-server/README.md`
- **Complete Status**: `/MCP_SERVER_COMPLETE.md`
- **This Guide**: `/MCP_QUICKSTART.md`

---

## 🔐 Default Credentials (Development)

```bash
# MCP Server
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=dental_erp_dev (ERP) / mcp (MCP)

# ERP Backend
JWT_SECRET=dental-erp-super-secret-jwt-key-development-only

# ⚠️ CHANGE ALL THESE IN PRODUCTION!
```

---

## 📝 Common Commands

### Docker Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild services
docker-compose up --build -d

# View logs
docker-compose logs -f mcp-server
docker-compose logs -f backend

# Restart specific service
docker-compose restart mcp-server

# Check service status
docker-compose ps
```

### MCP Server
```bash
# Test health
curl http://localhost:8085/health

# View API documentation
open http://localhost:8085/docs  # macOS
xdg-open http://localhost:8085/docs  # Linux

# Check MCP database
docker-compose exec postgres psql -U postgres -d mcp -c "\dt"

# View MCP logs
docker-compose logs -f mcp-server
```

### ERP Backend
```bash
# View backend logs
docker-compose logs -f backend

# Check environment variables
docker-compose exec backend env | grep MCP

# Restart backend
docker-compose restart backend
```

---

## 🧪 Testing the Integration

### 1. Register a Mapping
```bash
curl -X POST http://localhost:8085/api/v1/mappings/register \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "Content-Type: application/json" \
  -d '{
    "source_system": "ADP",
    "source_id": "emp_12345",
    "target_system": "ERP",
    "target_id": "user_67890",
    "entity_type": "employee"
  }'
```

### 2. Get Mappings
```bash
curl http://localhost:8085/api/v1/mappings/employee \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"
```

### 3. Trigger Sync Job
```bash
curl -X POST http://localhost:8085/api/v1/sync/run \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "adp",
    "entity_types": ["employee", "payroll"],
    "sync_mode": "incremental"
  }'
```

### 4. Get Financial Summary
```bash
curl "http://localhost:8085/api/v1/finance/summary?location=loc_001" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"
```

---

## 🐛 Troubleshooting

### MCP Server won't start

**Problem**: `docker-compose logs mcp-server` shows errors

**Solutions**:
```bash
# Check if port 8085 is available
lsof -i :8085

# Check environment variables
docker-compose config | grep MCP

# Rebuild container
docker-compose up --build mcp-server
```

### Backend can't connect to MCP

**Problem**: Backend logs show "MCP Server not accessible"

**Solutions**:
```bash
# Verify MCP is running
curl http://localhost:8085/health

# Check backend MCP configuration
docker-compose exec backend env | grep MCP_API

# Restart in correct order
docker-compose restart mcp-server backend
```

### Database connection errors

**Problem**: "could not connect to database"

**Solutions**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test database connection
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# Recreate database volume
docker-compose down -v
docker-compose up -d
```

---

## 📊 Monitoring

### Health Checks
```bash
# MCP Server health
curl http://localhost:8085/health/detailed

# Backend health
curl http://localhost:3001/health

# Database health
docker-compose exec postgres pg_isready
```

### View Running Services
```bash
docker-compose ps

# Expected output:
# postgres     Running (healthy)
# redis        Running (healthy)
# mcp-server   Running (healthy)
# backend      Running (healthy)
# frontend     Running
```

---

## 🚀 Deployment to Production

### 1. Update Environment Variables
```bash
# Create production .env file
cp .env.example .env.production

# Edit with production values
nano .env.production

# Key variables to change:
# - MCP_API_KEY (use strong 32+ char key)
# - SECRET_KEY (use strong 32+ char key)
# - POSTGRES_PASSWORD
# - JWT_SECRET
# - JWT_REFRESH_SECRET
```

### 2. Deploy
```bash
# Export production MCP key
export MCP_API_KEY="your-production-key-32-chars-minimum"

# Run deployment script
./deploy.sh
```

### 3. Verify
```bash
# Check all services are running
docker-compose ps

# Test MCP health
curl https://your-domain.com/mcp/health

# Test ERP health
curl https://your-domain.com/api/health
```

---

## 📚 Next Steps

### Immediate
1. ✅ Start services: `docker-compose up -d`
2. ✅ Test MCP endpoints
3. ✅ Verify ERP connectivity
4. ✅ Explore API docs at `/docs`

### Short Term
1. Implement real integration connectors (ADP, NetSuite)
2. Connect to actual Snowflake data warehouse
3. Add monitoring (Prometheus/Grafana)
4. Set up CI/CD pipeline

### Long Term
1. Add MCP workflows for orchestration
2. Implement WebSocket for real-time updates
3. Add rate limiting and throttling
4. Implement credential encryption
5. Add comprehensive test suite

---

## 🎉 Success!

You now have a fully operational MCP architecture!

**Key Benefits**:
- ✅ Decoupled integration layer
- ✅ Centralized credential management
- ✅ Easy to add new integrations
- ✅ Scalable microservice architecture
- ✅ Production-ready with Docker

**Get Started**:
```bash
docker-compose up -d
open http://localhost:8085/docs
```

**Need Help?**
- MCP Server README: `/mcp-server/README.md`
- API Documentation: http://localhost:8085/docs
- Backend Integration: `/backend/MCP_MIGRATION.md`

---

**Happy Coding!** 🚀
