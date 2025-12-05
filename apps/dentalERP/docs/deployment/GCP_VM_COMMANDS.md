# GCP VM Quick Command Reference

## Connect to VM

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a
```

## Deploy Demo (All-in-One)

```bash
cd /opt/dental-erp
sudo git pull origin main
sudo ./scripts/deploy-demo.sh
```

## Individual Commands

### Update Code

```bash
cd /opt/dental-erp
sudo git pull origin main
```

### Check Docker Status

```bash
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### View Logs

```bash
# Frontend
sudo docker logs --tail 100 dentalerp-frontend-prod-1

# Backend
sudo docker logs --tail 100 dentalerp-backend-prod-1

# MCP Server
sudo docker logs --tail 100 dentalerp-mcp-server-prod-1
```

### Restart Services

```bash
# Restart frontend only
sudo docker restart dentalerp-frontend-prod-1

# Restart all services
cd /opt/dental-erp
sudo ./deploy.sh
```

### Load Demo Data

```bash
cd /opt/dental-erp
source .env
sudo -E python3 scripts/ingest-netsuite-multi-practice.py
```

### Test Endpoints

```bash
# Frontend
curl -I https://dentalerp.agentprovision.com

# MCP Server health
curl https://mcp.agentprovision.com/health

# MCP Server API (requires MCP_API_KEY)
curl https://mcp.agentprovision.com/api/v1/analytics/financial/summary \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: eastlake"
```

### Environment Variables

```bash
# View current .env
cat /opt/dental-erp/.env | grep -v PASSWORD

# Source .env for current session
cd /opt/dental-erp
set -a
source .env
set +a
```

### Database Operations

```bash
# Backend PostgreSQL
sudo docker exec -it dentalerp-postgres-1 psql -U dentalerp -d dentalerp

# Check migrations
cd /opt/dental-erp/backend
npm run db:migrate
```

## Quick Fixes

### Frontend 502 Error

```bash
sudo docker restart dentalerp-frontend-prod-1
sleep 10
curl -I https://dentalerp.agentprovision.com
```

### MCP Server Not Responding

```bash
sudo docker restart dentalerp-mcp-server-prod-1
sleep 5
curl https://mcp.agentprovision.com/health
```

### Full System Restart

```bash
cd /opt/dental-erp
sudo docker-compose down
sudo ./deploy.sh
```

## Monitoring

### Check Disk Space

```bash
df -h
```

### Check Memory Usage

```bash
free -h
docker stats --no-stream
```

### Check Port Bindings

```bash
sudo netstat -tulpn | grep -E ':(3000|3001|8085|5432|6379)'
```

## File Locations

- **Project Root**: `/opt/dental-erp`
- **Environment**: `/opt/dental-erp/.env`
- **Nginx Config**: `/etc/nginx/sites-available/dentalerp`
- **SSL Certs**: `/etc/letsencrypt/live/dentalerp.agentprovision.com/`
- **Docker Volumes**: `/var/lib/docker/volumes/`

## Useful Aliases (Optional)

Add to `~/.bashrc`:

```bash
alias de='cd /opt/dental-erp'
alias dl='sudo docker logs --tail 100'
alias dp='sudo docker ps'
alias dr='sudo docker restart'
alias pull-deploy='cd /opt/dental-erp && sudo git pull && sudo ./deploy.sh'
```

Then: `source ~/.bashrc`

---

**Quick Start**: `gcloud compute ssh dental-erp-vm --zone=us-central1-a`
**Then run**: `cd /opt/dental-erp && sudo ./scripts/deploy-demo.sh`
