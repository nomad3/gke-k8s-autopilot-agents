# DentalERP Deployment Guide

## Overview

DentalERP uses Docker Compose for containerized deployment with support for both local development and production VM deployment with Nginx + SSL.

## Quick Start

### Local Development
```bash
./deploy.sh
```

### Production Deployment
```bash
# On production server
export MCP_API_KEY="your-secure-32+-char-key"
export MCP_SECRET_KEY="your-secure-32+-char-jwt-secret"
export SNOWFLAKE_ACCOUNT="your-snowflake-account"
export SNOWFLAKE_USER="your-snowflake-user"
export SNOWFLAKE_PASSWORD="your-snowflake-password"

./deploy.sh
```

## Architecture

**Services:**
- `postgres` - PostgreSQL 15 database (ports: 5432)
- `redis` - Redis cache (port: 6379)
- `mcp-server-prod` - FastAPI MCP server (port: 8085)
- `backend-prod` - Express.js API (port: 3001)
- `frontend-prod` - React SPA with Nginx (port: 3000)

**Domains (Production):**
- Frontend: https://dentalerp.agentprovision.com
- MCP Server: https://mcp.agentprovision.com

## Configuration

### Environment Variables

**Required for Production:**
```bash
MCP_API_KEY=<32+ character secure key>
MCP_SECRET_KEY=<32+ character JWT secret>
```

**Optional - Snowflake Integration:**
```bash
SNOWFLAKE_ACCOUNT=<account-id>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<password>
SNOWFLAKE_WAREHOUSE=COMPUTE_WH  # optional, defaults to COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW  # optional
SNOWFLAKE_SCHEMA=PUBLIC  # optional
SNOWFLAKE_ROLE=ACCOUNTADMIN  # optional
```

**Optional - OpenAI (for PDF extraction):**
```bash
OPENAI_API_KEY=sk-...
```

### Deployment Script Features

The `deploy.sh` script handles:
1. **Prerequisite checks** - Verifies Docker, Docker Compose, Nginx, Certbot
2. **Service deployment** - Builds and starts all containers
3. **Nginx configuration** - Sets up reverse proxy with SSL
4. **SSL certificates** - Automatically requests/renews Let's Encrypt certificates
5. **Snowflake setup** - Configures tenant warehouse if credentials provided
6. **Health checks** - Waits for services to be ready
7. **E2E testing** - Runs production tests if available

## First-Time Setup

### 1. Prerequisites

**Local Development:**
- Docker 20.10+
- Docker Compose 1.29+

**Production Server:**
- Docker 20.10+
- Docker Compose 1.29+
- Nginx 1.18+
- Certbot (for SSL certificates)
- Domain DNS configured to point to server IP

### 2. Clone Repository
```bash
git clone https://github.com/yourusername/dentalERP.git
cd dentalERP
```

### 3. Configure Secrets

**For production, NEVER commit secrets to git.** Export them as environment variables:

```bash
# Generate secure keys (32+ characters)
export MCP_API_KEY=$(openssl rand -hex 32)
export MCP_SECRET_KEY=$(openssl rand -hex 32)

# Add Snowflake credentials if needed
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-user"
export SNOWFLAKE_PASSWORD="your-password"
```

### 4. Run Deployment
```bash
./deploy.sh
```

## Manual Deployment Steps

If you need to run steps manually:

### 1. Build and Start Services
```bash
docker-compose --profile production up --build -d
```

### 2. Check Service Status
```bash
docker ps --filter "name=dentalerp"
```

### 3. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server-prod
docker-compose logs -f backend-prod
docker-compose logs -f frontend-prod
```

### 4. Setup Snowflake (if needed)
```bash
# Export credentials first
export SNOWFLAKE_ACCOUNT="..."
export SNOWFLAKE_USER="..."
export SNOWFLAKE_PASSWORD="..."

# Run setup
docker exec dental-erp_postgres_1 psql -U postgres -d mcp << 'EOSQL'
INSERT INTO tenant_warehouses (
  id, tenant_id, warehouse_type, warehouse_config, is_primary, is_active
)
SELECT
  gen_random_uuid(), id, 'snowflake',
  jsonb_build_object(
    'account', 'your-account',
    'user', 'your-user',
    'warehouse', 'COMPUTE_WH',
    'database', 'DENTAL_ERP_DW',
    'schema', 'PUBLIC',
    'role', 'ACCOUNTADMIN'
  ),
  true, true
FROM tenants
WHERE tenant_code = 'default'
ON CONFLICT DO NOTHING;
EOSQL
```

## Troubleshooting

### Services Won't Start

**Check logs:**
```bash
docker-compose logs mcp-server-prod
docker-compose logs backend-prod
```

**Common issues:**
- Port conflicts: Check if ports 3000, 3001, 8085 are available
- Database not ready: Wait a few seconds for postgres to initialize
- Missing environment variables: Ensure all required vars are exported

### Database Issues

**Reset database:**
```bash
docker-compose down -v  # WARNING: Deletes all data
docker-compose --profile production up -d
```

**Access database:**
```bash
# Backend database
docker exec dental-erp_postgres_1 psql -U postgres -d dental_erp_dev

# MCP database
docker exec dental-erp_postgres_1 psql -U postgres -d mcp
```

### Snowflake Connection Issues

**Verify credentials in container:**
```bash
docker exec dental-erp_mcp-server-prod_1 printenv | grep SNOWFLAKE
```

**Check warehouse configuration:**
```bash
docker exec dental-erp_postgres_1 psql -U postgres -d mcp -c \
  "SELECT tenant_code, warehouse_type, is_active FROM tenant_warehouses tw
   JOIN tenants t ON tw.tenant_id = t.id WHERE tenant_code = 'default';"
```

**Test analytics endpoint:**
```bash
curl -s \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  "https://mcp.agentprovision.com/api/v1/analytics/production/summary"
```

### SSL Certificate Issues

**Manually request certificate:**
```bash
sudo certbot --nginx -d dentalerp.agentprovision.com --email your@email.com
sudo certbot --nginx -d mcp.agentprovision.com --email your@email.com
```

**Renew certificates:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Maintenance

### Update Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose --profile production up --build -d
```

### Backup Database

```bash
# Backup
docker exec dental-erp_postgres_1 pg_dump -U postgres dental_erp_dev > backup.sql

# Restore
docker exec -i dental-erp_postgres_1 psql -U postgres dental_erp_dev < backup.sql
```

### Monitor Disk Usage

```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
docker system prune -a -f
```

### View Service Health

```bash
# Backend health
curl https://dentalerp.agentprovision.com/api/health

# MCP health
curl https://mcp.agentprovision.com/health
```

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Use strong keys** - Generate with `openssl rand -hex 32`
3. **Keep software updated** - Regularly pull latest Docker images
4. **Monitor logs** - Check for suspicious activity
5. **Backup regularly** - Automate database backups
6. **Use SSL** - Always deploy with HTTPS in production
7. **Rotate keys** - Change API keys periodically

## Production Checklist

Before going live:

- [ ] DNS records configured for both domains
- [ ] Environment variables set (MCP_API_KEY, MCP_SECRET_KEY)
- [ ] Snowflake credentials configured (if using)
- [ ] SSL certificates obtained and valid
- [ ] All services healthy and responding
- [ ] Database migrations applied
- [ ] E2E tests passing
- [ ] Monitoring/alerting configured
- [ ] Backup strategy in place
- [ ] Firewall rules configured
- [ ] Default passwords changed

## Support

For issues or questions:
- **Documentation**: See CLAUDE.md for codebase details
- **GitHub Issues**: https://github.com/yourusername/dentalERP/issues
- **Logs**: Always check `docker-compose logs` first

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Port 80/443)                       │
│  ┌──────────────────────┐    ┌──────────────────────────┐   │
│  │ dentalerp            │    │ mcp.agentprovision.com   │   │
│  │ .agentprovision.com  │    │                          │   │
│  └──────────┬───────────┘    └──────────┬───────────────┘   │
└─────────────┼──────────────────────────┼────────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────┐  ┌──────────────────────────────┐
│  Frontend (Port 3000)   │  │  MCP Server (Port 8085)      │
│  - React SPA            │  │  - FastAPI                    │
│  - Vite build           │  │  - Multi-tenant               │
│  - Nginx serve          │  │  - PDF AI extraction          │
└─────────────────────────┘  │  - Warehouse routing          │
              │              │  - Integration routing         │
              ▼              └────────┬─────────────────────┬─┘
┌─────────────────────────┐          │                     │
│  Backend (Port 3001)    │          │                     │
│  - Express.js API       │◄─────────┘                     │
│  - JWT auth             │                                │
│  - Business logic       │                                ▼
└──────┬──────────┬───────┘                  ┌──────────────────────┐
       │          │                          │  Snowflake DW        │
       │          │                          │  - Bronze/Silver/Gold│
       ▼          ▼                          │  - dbt transformations│
┌──────────┐  ┌─────────┐                   └──────────────────────┘
│PostgreSQL│  │  Redis  │
│ (5432)   │  │ (6379)  │
└──────────┘  └─────────┘
```
