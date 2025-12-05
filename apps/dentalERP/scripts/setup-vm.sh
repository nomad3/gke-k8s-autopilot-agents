#!/bin/bash
# Quick setup script for Google Cloud VM deployment
# Run this after cloning the repository to /opt/dental-erp

set -e

# Domain for nginx/certbot. Override by running: DOMAIN=app.yourdomain.com ./setup-vm.sh
DOMAIN="${DOMAIN:-dentalerp.example.com}"

echo "🚀 Setting up Dental ERP on VM..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /opt/dental-erp/backups
mkdir -p /opt/dental-erp/logs/backend
mkdir -p /opt/dental-erp/logs/nginx

# Generate secure secrets
echo "🔐 Generating secure secrets..."
JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
JWT_REFRESH_SECRET=$(openssl rand -base64 64 | tr -d '\n')
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')

# Get VM's external IP (if on GCP)
EXTERNAL_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null || echo "YOUR_IP_OR_DOMAIN")

# Create .env.production file
echo "📝 Creating .env.production file..."
cat > /opt/dental-erp/.env.production <<EOF
# Database Configuration
POSTGRES_DB=dental_erp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@dental-erp-postgres:5432/dental_erp

# Redis Configuration
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@dental-erp-redis:6379

# JWT Secrets (Keep these secure!)
JWT_SECRET=${JWT_SECRET}
JWT_REFRESH_SECRET=${JWT_REFRESH_SECRET}

# Application Configuration
NODE_ENV=production
FRONTEND_URL=https://${DOMAIN}
VITE_API_BASE_URL=/api

# Feature Flags
MOCK_INTEGRATIONS=true
ENABLE_AUDIT_LOGGING=true

# Optional: Monitoring (add your keys)
SENTRY_DSN=

# Optional: Email notifications
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@yourdomain.com
EOF

echo "✅ .env.production created!"
echo ""
echo "🌐 Domain configured for nginx: ${DOMAIN}"

# Install nginx + certbot and configure reverse proxy
echo "🧰 Installing nginx and certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

echo "🧼 Cleaning default nginx site and creating dental-erp config..."
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/dental-erp.conf <<NGINXCONF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /api/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade           \$http_upgrade;
        proxy_set_header Connection        \$connection_upgrade;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade           \$http_upgrade;
        proxy_set_header Connection        \$connection_upgrade;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade           \$http_upgrade;
        proxy_set_header Connection        \$connection_upgrade;
    }
}
NGINXCONF

ln -sf /etc/nginx/sites-available/dental-erp.conf /etc/nginx/sites-enabled/dental-erp.conf
nginx -t
systemctl reload nginx

# Open firewall ports 80/443 if possible
if command -v gcloud >/dev/null 2>&1; then
  echo "🔓 Ensuring GCP firewall rules allow HTTP/HTTPS..."
  gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --direction INGRESS \
    --target-tags http-server \
    --priority 1000 \
    2>/dev/null || true

  gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --direction INGRESS \
    --target-tags https-server \
    --priority 1000 \
    2>/dev/null || true
else
  echo "🔓 Allowing ports 80/443 via ufw (if available)..."
  if command -v ufw >/dev/null 2>&1; then
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true
  fi
fi

echo "⚠️  IMPORTANT: Save these credentials securely!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Database Password: ${POSTGRES_PASSWORD}"
echo "Redis Password: ${REDIS_PASSWORD}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your application will be accessible at: http://${EXTERNAL_IP}"
echo ""
echo "📋 Next steps:"
echo "1. Point your DNS A record to ${EXTERNAL_IP}"
echo "2. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "3. Obtain TLS certificate: sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "To restart: docker-compose -f docker-compose.prod.yml restart"
echo ""
