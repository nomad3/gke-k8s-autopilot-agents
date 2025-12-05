# Deploying Dental ERP to Google Cloud VM

This guide covers deploying your Dental ERP SaaS to a Google Cloud Compute Engine VM.

## 💰 Cost Estimate

### Recommended Configuration (Small Production)
```
VM Instance:    e2-small (2 vCPU, 2GB RAM)      $12-15/month
Disk:           30GB SSD                         $5/month
IP Address:     Static External IP               $3/month
Total:          ~$20-23/month (with sustained use discount)
```

### Can Handle:
- **500-2000 concurrent users**
- **5-10K requests/minute**
- **Perfect for MVP to early growth stage**

---

## 🚀 Quick Deploy (15 Minutes)

### Step 1: Create GCP VM

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Create VM instance
gcloud compute instances create dental-erp-vm \
  --zone=us-central1-a \
  --machine-type=e2-small \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-ssd \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose git
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu'
```

### Step 2: Configure Firewall

```bash
# Allow HTTP traffic
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags http-server

# Allow HTTPS traffic
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --target-tags https-server

# Optional: Allow SSH from your IP only (more secure)
gcloud compute firewall-rules create allow-ssh-from-my-ip \
  --allow tcp:22 \
  --source-ranges YOUR_IP_ADDRESS/32
```

### Step 3: Reserve Static IP

```bash
# Reserve static IP
gcloud compute addresses create dental-erp-ip --region=us-central1

# Get the IP address
gcloud compute addresses describe dental-erp-ip --region=us-central1

# Assign to your VM
gcloud compute instances delete-access-config dental-erp-vm --zone=us-central1-a
gcloud compute instances add-access-config dental-erp-vm \
  --zone=us-central1-a \
  --address=$(gcloud compute addresses describe dental-erp-ip --region=us-central1 --format="value(address)")
```

### Step 4: SSH into VM and Deploy

```bash
# SSH into your VM
gcloud compute ssh dental-erp-vm --zone=us-central1-a

# Once inside the VM, run these commands:

# Clone your repository
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/dentalERP.git
cd dentalERP

# Generate secure secrets
export JWT_SECRET=$(openssl rand -base64 64)
export JWT_REFRESH_SECRET=$(openssl rand -base64 64)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)

# Create production environment file
sudo tee .env.production > /dev/null <<EOF
# Database
POSTGRES_DB=dental_erp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/dental_erp

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

# JWT Secrets
JWT_SECRET=${JWT_SECRET}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}

# Application
NODE_ENV=production
FRONTEND_URL=http://YOUR_DOMAIN_OR_IP
VITE_API_BASE_URL=http://YOUR_DOMAIN_OR_IP/api
MOCK_INTEGRATIONS=true
ENABLE_AUDIT_LOGGING=true
EOF

# Start the application
sudo docker-compose -f docker-compose.prod.yml up -d

# Check status
sudo docker-compose -f docker-compose.prod.yml ps
```

### Step 5: Set Up Domain (Optional but Recommended)

```bash
# Point your domain to the VM's IP address
# Add A record in your DNS provider:
# Type: A
# Name: @ (or subdomain)
# Value: YOUR_VM_IP_ADDRESS

# Install Certbot for SSL
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 📦 Complete Setup Script

Save this as `setup-gcp.sh` and run it:

```bash
#!/bin/bash
set -e

echo "🚀 Setting up Dental ERP on Google Cloud VM..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Install nginx
echo "📡 Installing Nginx..."
sudo apt-get install -y nginx

# Install certbot for SSL
echo "🔒 Installing Certbot..."
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Install monitoring tools
echo "📊 Installing monitoring tools..."
sudo apt-get install -y htop iotop netdata

# Configure firewall
echo "🔥 Configuring UFW firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 19999/tcp # Netdata (monitoring)

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/dental-erp
sudo chown -R $USER:$USER /opt/dental-erp

# Install fail2ban for security
echo "🛡️ Installing fail2ban..."
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository to /opt/dental-erp"
echo "2. Create .env.production file"
echo "3. Run: cd /opt/dental-erp && docker-compose -f docker-compose.prod.yml up -d"
echo "4. Configure SSL: sudo certbot --nginx -d yourdomain.com"
```

---

## 🔒 Nginx Configuration

Create `/etc/nginx/sites-available/dental-erp`:

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main Application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Certbot will add this)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;

    # Frontend (Static Files)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket Support
    location /socket.io {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health Check
    location /health {
        proxy_pass http://localhost:3001/health;
        access_log off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/dental-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔄 Automatic Deployment Script

Create `/opt/dental-erp/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying Dental ERP..."

# Navigate to app directory
cd /opt/dental-erp

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Backup database
echo "💾 Backing up database..."
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres dental_erp | gzip > backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Build and restart services
echo "🔨 Building and restarting services..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
echo "🗃️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend npm run db:push

# Clean up old images
echo "🧹 Cleaning up..."
docker image prune -f

# Check health
echo "🏥 Checking application health..."
sleep 10
curl -f http://localhost:3001/health || echo "⚠️ Health check failed"

echo "✅ Deployment complete!"
```

Make it executable:
```bash
chmod +x /opt/dental-erp/deploy.sh
```

---

## 📊 Monitoring Setup

### Install Netdata (Real-time Monitoring)

```bash
# Install Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Configure firewall
sudo ufw allow 19999/tcp

# Access at: http://YOUR_IP:19999
```

### Set Up Google Cloud Monitoring

```bash
# Install Cloud Ops Agent
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure logging
sudo tee /etc/google-cloud-ops-agent/config.yaml > /dev/null <<EOF
logging:
  receivers:
    syslog:
      type: files
      include_paths:
        - /var/log/syslog
        - /var/log/nginx/*.log
        - /opt/dental-erp/logs/*.log
  service:
    pipelines:
      default_pipeline:
        receivers: [syslog]
EOF

sudo systemctl restart google-cloud-ops-agent
```

---

## 💾 Automated Backups

Create `/opt/dental-erp/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/dental-erp/backups"
BACKUP_RETENTION_DAYS=30
GCS_BUCKET="gs://your-backup-bucket"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose -f /opt/dental-erp/docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres dental_erp | gzip > $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz

# Backup uploaded files (if any)
echo "Backing up files..."
tar -czf $BACKUP_DIR/files_backup_$TIMESTAMP.tar.gz /opt/dental-erp/uploads 2>/dev/null || true

# Upload to Google Cloud Storage
echo "Uploading to GCS..."
gsutil cp $BACKUP_DIR/*_$TIMESTAMP.* $GCS_BUCKET/

# Clean up old local backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete

echo "Backup complete!"
```

Set up cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * /opt/dental-erp/backup.sh >> /var/log/dental-erp-backup.log 2>&1
```

---

## 🔐 Security Hardening

### 1. SSH Hardening

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Set these values:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Change SSH port

# Restart SSH
sudo systemctl restart sshd
```

### 2. Fail2ban Configuration

```bash
# Create jail for nginx
sudo tee /etc/fail2ban/jail.d/nginx.conf > /dev/null <<EOF
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
findtime = 60
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

### 3. Set Up Secret Management

```bash
# Install Google Secret Manager (optional)
gcloud secrets create dental-erp-jwt-secret --data-file=- <<< "$JWT_SECRET"
gcloud secrets create dental-erp-db-password --data-file=- <<< "$POSTGRES_PASSWORD"
```

---

## 📈 Scaling Options

### Vertical Scaling (Upgrade VM)

```bash
# Stop VM
gcloud compute instances stop dental-erp-vm --zone=us-central1-a

# Change machine type
gcloud compute instances set-machine-type dental-erp-vm \
  --machine-type=e2-medium \
  --zone=us-central1-a

# Start VM
gcloud compute instances start dental-erp-vm --zone=us-central1-a
```

### Add Read Replica (for high traffic)

```bash
# Create separate database VM
# Configure PostgreSQL replication
# Update app to use read replica for queries
```

---

## 💰 Cost Optimization Tips

1. **Use Preemptible VMs for dev/staging** (80% cheaper)
   ```bash
   --preemptible
   ```

2. **Use committed use discounts** (save up to 57%)
   - 1-year commitment: ~30% discount
   - 3-year commitment: ~57% discount

3. **Right-size your VM**
   - Start with e2-small
   - Monitor with Netdata
   - Scale up only when needed

4. **Use Cloud CDN** for static assets
   ```bash
   gcloud compute backend-services add-backend dental-erp-backend \
     --enable-cdn
   ```

---

## 🚨 Troubleshooting

### VM is slow
```bash
# Check resource usage
htop
docker stats

# Check disk space
df -h

# Check network
iftop
```

### Database issues
```bash
# Check postgres logs
docker-compose -f docker-compose.prod.yml logs postgres

# Check connections
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### Can't connect to VM
```bash
# Check firewall rules
gcloud compute firewall-rules list

# Check VM status
gcloud compute instances list

# Check SSH connectivity
gcloud compute ssh dental-erp-vm --zone=us-central1-a --troubleshoot
```

---

## 📋 Maintenance Checklist

### Daily
- [ ] Check application logs
- [ ] Monitor resource usage (Netdata)
- [ ] Verify backups ran successfully

### Weekly
- [ ] Update system packages
- [ ] Review security logs
- [ ] Check disk space
- [ ] Test backup restoration

### Monthly
- [ ] Update Docker images
- [ ] Review and optimize costs
- [ ] Run security audit
- [ ] Load testing

---

## 🎯 Next Steps

1. **Set up monitoring alerts**
   ```bash
   # Configure alerting in Cloud Monitoring
   gcloud alpha monitoring policies create
   ```

2. **Set up CI/CD**
   - Use GitHub Actions to deploy on push
   - See `.github/workflows/deploy.yml`

3. **Add more VMs for high availability**
   - Set up load balancer
   - Configure health checks
   - Use managed instance groups

4. **Migrate to Cloud SQL** (when you scale)
   - Managed PostgreSQL
   - Automatic backups
   - High availability

---

## 📞 Useful Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
cd /opt/dental-erp && git pull && docker-compose -f docker-compose.prod.yml up -d --build

# Check resource usage
gcloud compute instances describe dental-erp-vm --zone=us-central1-a

# SSH into VM
gcloud compute ssh dental-erp-vm --zone=us-central1-a

# Copy files to VM
gcloud compute scp local-file.txt dental-erp-vm:/opt/dental-erp/ --zone=us-central1-a
```

---

**Total Monthly Cost: ~$20-25 for small VM + excellent performance!** 🎉
