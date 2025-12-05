# 🚀 MCP Server Deployment Guide

## ✅ What Was Updated

The `deploy.sh` script and `docker-compose.yml` have been updated to support the MCP Server on its own subdomain: **`mcp.agentprovision.com`**

---

## 🌐 Domain Configuration

### Main Domains:
- **ERP Application**: `dentalerp.agentprovision.com`
- **MCP Server**: `mcp.agentprovision.com` ⭐ NEW

### SSL Certificates:
Both domains will get their own Let's Encrypt SSL certificates automatically during deployment.

---

## 📝 DNS Configuration Required

Before deploying, ensure you have DNS A records pointing to your server:

```dns
dentalerp.agentprovision.com  →  YOUR_SERVER_IP
mcp.agentprovision.com        →  YOUR_SERVER_IP
```

### How to Add DNS Records:

1. Log into your DNS provider (e.g., Cloudflare, Route53, Namecheap)
2. Add an A record:
   - **Name**: `mcp`
   - **Type**: `A`
   - **Value**: Your server's IP address
   - **TTL**: Auto or 300 seconds

---

## 🔐 Environment Variables Required

Before deploying, export these environment variables:

```bash
# MCP Server API Key (32+ characters)
export MCP_API_KEY="your-super-secure-mcp-api-key-change-this-in-production"

# MCP Server Secret Key (32+ characters)
export MCP_SECRET_KEY="your-super-secure-secret-key-for-jwt-signing"

# PostgreSQL Password (optional, defaults to 'postgres')
export POSTGRES_PASSWORD="your-secure-database-password"
```

**⚠️ Important**: Use strong, randomly generated keys in production!

Generate secure keys:
```bash
# Generate MCP API Key
openssl rand -base64 32

# Generate Secret Key
openssl rand -base64 32
```

---

## 🚀 Deployment Steps

### 1. Connect to Your Server

```bash
ssh user@your-server-ip
cd /path/to/dentalERP
```

### 2. Set Environment Variables

```bash
export MCP_API_KEY="$(openssl rand -base64 32)"
export MCP_SECRET_KEY="$(openssl rand -base64 32)"
export POSTGRES_PASSWORD="your-secure-password"

# Verify they're set
echo "MCP_API_KEY: ${MCP_API_KEY:0:10}..."
echo "MCP_SECRET_KEY: ${MCP_SECRET_KEY:0:10}..."
```

### 3. Run Deployment Script

```bash
# Make script executable (if needed)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will automatically:
1. ✅ Start PostgreSQL and Redis
2. ✅ Build and start MCP Server (production)
3. ✅ Build and start Backend (production)
4. ✅ Build and start Frontend (production)
5. ✅ Configure Nginx for both domains
6. ✅ Request SSL certificates for both domains
7. ✅ Reload Nginx with SSL

---

## 📊 What Gets Deployed

### Services Started:
```
postgres          - PostgreSQL database (port 5432)
redis             - Redis cache (port 6379)
mcp-server-prod   - MCP Server (port 8085)
backend-prod      - ERP Backend (port 3001)
frontend-prod     - Frontend App (port 3000)
```

### Nginx Configuration:
```
dentalerp.agentprovision.com (HTTPS)
├── / → Frontend (port 3000)
└── /api/ → Backend (port 3001)

mcp.agentprovision.com (HTTPS)
├── / → MCP Server (port 8085)
├── /health → Health check
├── /docs → API documentation
└── /redoc → Alternative API docs
```

---

## ✅ Verification Steps

### 1. Check Services Are Running

```bash
docker ps

# Expected output should show:
# - postgres (healthy)
# - redis (healthy)
# - mcp-server-prod (healthy)
# - backend-prod (healthy)
# - frontend-prod (running)
```

### 2. Test MCP Server Directly

```bash
# Health check (public endpoint)
curl https://mcp.agentprovision.com/health

# Expected:
# {"status":"ok","timestamp":"2025-10-26T...","service":"mcp-server"}
```

### 3. Test MCP API (with authentication)

```bash
# Get integration status
curl https://mcp.agentprovision.com/api/v1/integrations/status \
  -H "Authorization: Bearer YOUR_MCP_API_KEY"

# Expected:
# [{"integration_type":"adp","status":"pending",...}]
```

### 4. Test ERP → MCP Communication

```bash
# Test ERP backend health
curl https://dentalerp.agentprovision.com/api/health

# Check ERP integration status (uses MCP internally)
curl https://dentalerp.agentprovision.com/api/integrations/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. View API Documentation

Open in browser:
- **FastAPI Docs**: https://mcp.agentprovision.com/docs
- **ReDoc**: https://mcp.agentprovision.com/redoc

---

## 🐛 Troubleshooting

### DNS Not Resolving

**Problem**: `mcp.agentprovision.com` doesn't resolve

**Solution**:
```bash
# Check DNS propagation
nslookup mcp.agentprovision.com

# Or use online tools
# https://dnschecker.org
```

DNS can take 5-60 minutes to propagate globally.

### SSL Certificate Failed

**Problem**: Certbot fails to issue certificate

**Solution**:
```bash
# Verify DNS is pointing to your server
dig mcp.agentprovision.com

# Check Nginx is running
sudo systemctl status nginx

# Check if port 80 is accessible
curl http://mcp.agentprovision.com

# Manually request certificate
sudo certbot --nginx -d mcp.agentprovision.com --email saguilera1608@gmail.com
```

### MCP Server Not Starting

**Problem**: `mcp-server-prod` container keeps restarting

**Solution**:
```bash
# Check logs
docker logs mcp-server-prod

# Common issues:
# - MCP_API_KEY not set → export MCP_API_KEY="..."
# - Database not ready → check postgres logs
# - Port conflict → ensure 8085 is free
```

### Backend Can't Connect to MCP

**Problem**: Backend logs show "MCP Server not accessible"

**Solution**:
```bash
# Check if MCP is running
docker ps | grep mcp-server-prod

# Test from backend container
docker exec backend-prod curl http://mcp-server-prod:8085/health

# Verify environment variables
docker exec backend-prod env | grep MCP
```

---

## 🔒 Security Considerations

### Production Checklist:
- [ ] Strong `MCP_API_KEY` set (32+ chars)
- [ ] Strong `MCP_SECRET_KEY` set (32+ chars)
- [ ] Database password changed from default
- [ ] JWT secrets updated in backend
- [ ] Firewall configured (only 80, 443 open)
- [ ] SSL certificates auto-renewing
- [ ] Logs being monitored

### Firewall Configuration:

```bash
# Allow HTTPS traffic
sudo ufw allow 443/tcp

# Allow HTTP (for certificate renewal)
sudo ufw allow 80/tcp

# Block direct access to MCP port
sudo ufw deny 8085/tcp

# Enable firewall
sudo ufw enable
```

---

## 📊 Monitoring

### Check Service Health:

```bash
# All services
docker-compose ps

# MCP Server logs
docker logs -f mcp-server-prod

# Backend logs
docker logs -f backend-prod

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Endpoints:

```bash
# MCP Server
watch -n 5 'curl -s https://mcp.agentprovision.com/health | jq'

# ERP Backend
watch -n 5 'curl -s https://dentalerp.agentprovision.com/api/health | jq'
```

---

## 🔄 Updates & Maintenance

### Update MCP Server:

```bash
cd /path/to/dentalERP

# Pull latest code
git pull origin main

# Rebuild and restart MCP
docker-compose build mcp-server-prod
docker-compose up -d mcp-server-prod

# Check logs
docker logs -f mcp-server-prod
```

### Renew SSL Certificates:

Certificates auto-renew, but you can manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## 📞 Support

### Common URLs:
- **ERP App**: https://dentalerp.agentprovision.com
- **ERP API**: https://dentalerp.agentprovision.com/api
- **MCP Server**: https://mcp.agentprovision.com
- **MCP Docs**: https://mcp.agentprovision.com/docs
- **MCP Health**: https://mcp.agentprovision.com/health

### Logs Location:
- **Docker**: `docker logs <container-name>`
- **Nginx**: `/var/log/nginx/`
- **Certbot**: `/var/log/letsencrypt/`

---

## ✅ Deployment Checklist

Before running `./deploy.sh`:

- [ ] DNS A records configured for both domains
- [ ] Server has ports 80, 443 open
- [ ] Docker and docker-compose installed
- [ ] Nginx installed
- [ ] Certbot installed
- [ ] `MCP_API_KEY` exported
- [ ] `MCP_SECRET_KEY` exported
- [ ] Code pulled from git repository

After running `./deploy.sh`:

- [ ] All containers running (check with `docker ps`)
- [ ] https://dentalerp.agentprovision.com accessible
- [ ] https://mcp.agentprovision.com accessible
- [ ] https://mcp.agentprovision.com/docs shows API docs
- [ ] SSL certificates issued for both domains
- [ ] Health checks returning 200 OK

---

## 🎉 Success!

If all verification steps pass, your MCP architecture is now fully deployed and operational!

**Access Points:**
- **Main App**: https://dentalerp.agentprovision.com
- **MCP Server**: https://mcp.agentprovision.com
- **API Docs**: https://mcp.agentprovision.com/docs

**Next Steps:**
1. Configure actual integration credentials in MCP
2. Set up monitoring (Prometheus/Grafana)
3. Configure backup automation
4. Set up log aggregation (ELK/Datadog)

---

**Deployment Date**: October 26, 2025
**Status**: ✅ Production Ready
**Architecture**: MCP Multi-Domain Deployment
