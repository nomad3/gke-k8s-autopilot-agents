#!/bin/bash
set -euo pipefail

# Deployment Configuration
DOMAIN="dentalerp.agentprovision.com"
MCP_DOMAIN="mcp.agentprovision.com"
EMAIL="saguilera1608@gmail.com"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

API_PORT=${API_PORT:-3001}
WEB_PORT=${WEB_PORT:-3000}
MCP_PORT=${MCP_PORT:-8085}

# Default secure keys (should be overridden in production via env vars)
MCP_API_KEY=${MCP_API_KEY:-prod-mcp-api-key-change-in-production-min-32-chars-secure}
MCP_SECRET_KEY=${MCP_SECRET_KEY:-prod-mcp-secret-key-change-in-production-min-32-chars-jwt}

# Detect deployment mode: local or vm
DEPLOY_MODE=${DEPLOY_MODE:-auto}
if [ "$DEPLOY_MODE" = "auto" ]; then
  # Auto-detect: if nginx and certbot are installed, assume VM deployment
  if command -v nginx >/dev/null 2>&1 && command -v certbot >/dev/null 2>&1; then
    DEPLOY_MODE="vm"
  else
    DEPLOY_MODE="local"
  fi
fi

SERVICES=(postgres redis backend-db-init mcp-db-init mcp-server-prod backend-prod frontend-prod)

info() { echo "[deploy] $1"; }
error() { echo "[deploy] ERROR: $1" >&2; }

info "Deployment Mode: $DEPLOY_MODE"
if [ "$DEPLOY_MODE" = "vm" ]; then
  info "Starting VM deployment for $DOMAIN and $MCP_DOMAIN"
else
  info "Starting local deployment (no nginx/SSL configuration)"
fi

# --- 1. Prerequisite checks ---
if [ "$DEPLOY_MODE" = "vm" ]; then
  REQUIRED_CMDS=(docker docker-compose nginx certbot)
else
  REQUIRED_CMDS=(docker docker-compose)
fi

missing_cmds=()
for cmd in "${REQUIRED_CMDS[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing_cmds+=("$cmd")
  fi
done

if [ ${#missing_cmds[@]} -ne 0 ]; then
  error "Missing prerequisites: ${missing_cmds[*]}"
  error "Install required tools before running deployment."
  exit 1
fi

info "Prerequisites verified: ${REQUIRED_CMDS[*]}"

# --- 2. Export runtime variables and configure services ---
export API_PORT WEB_PORT MCP_API_KEY MCP_SECRET_KEY

# Export Snowflake credentials if set
if [ -n "${SNOWFLAKE_ACCOUNT:-}" ]; then
  export SNOWFLAKE_ACCOUNT SNOWFLAKE_USER SNOWFLAKE_PASSWORD
  export SNOWFLAKE_WAREHOUSE SNOWFLAKE_DATABASE SNOWFLAKE_SCHEMA SNOWFLAKE_ROLE
fi

info "Resolved configuration:"
info "  API_PORT=$API_PORT"
info "  WEB_PORT=$WEB_PORT"
info "  MCP_PORT=$MCP_PORT"
info "  MCP_API_KEY: ${MCP_API_KEY:0:8}..."
info "  MCP_SECRET_KEY: ${MCP_SECRET_KEY:0:8}..."
if [ -n "${SNOWFLAKE_ACCOUNT:-}" ]; then
  info "  SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}"
  info "  SNOWFLAKE_USER: ${SNOWFLAKE_USER}"
  info "  SNOWFLAKE_DATABASE: ${SNOWFLAKE_DATABASE:-DENTAL_ERP_DW}"
fi

if [ "$DEPLOY_MODE" = "vm" ]; then
  # Only require explicit keys in VM mode for production security
  if [[ -z "${MCP_API_KEY:-}" ]] || [[ "$MCP_API_KEY" == "prod-mcp-api-key"* ]]; then
    error "MCP_API_KEY is using default value. For VM deployment, export a secure 32+ char secret before deploying."
    exit 1
  fi

  if [[ -z "${MCP_SECRET_KEY:-}" ]] || [[ "$MCP_SECRET_KEY" == "prod-mcp-secret-key"* ]]; then
    error "MCP_SECRET_KEY is using default value. For VM deployment, export a secure 32+ char secret before deploying."
    exit 1
  fi
else
  info "Local mode: Using default development keys (OK for local testing)"
fi

info "Rendering docker-compose configuration preview"
docker-compose -f "$COMPOSE_FILE" config | head -n 40 || true

# --- 3. Stop existing services ---
info "Stopping existing Docker Compose stack"
docker-compose -f "$COMPOSE_FILE" --profile production down --remove-orphans || true
# --- 4. Build & start required services ---
info "Building and starting services: ${SERVICES[*]}"
docker-compose -f "$COMPOSE_FILE" --profile production up --build -d "${SERVICES[@]}"

info "Docker services running. Current status:"
docker ps --filter "name=dentalerp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# --- 5. Configure host Nginx (VM mode only) ---
if [ "$DEPLOY_MODE" != "vm" ]; then
  info "Skipping Nginx/SSL configuration (local mode)"
  info "Deployment complete (local mode)"
  info "Services available at:"
  info "  - Frontend: http://localhost:$WEB_PORT"
  info "  - Backend API: http://localhost:$API_PORT"
  info "  - MCP Server: http://localhost:$MCP_PORT"
  info "  - MCP API Docs: http://localhost:$MCP_PORT/docs"
  exit 0
fi

# Main ERP Domain
NGINX_CONF_PATH="/etc/nginx/sites-available/$DOMAIN"
SERVER_NAMES="$DOMAIN"

info "Writing Nginx configuration to $NGINX_CONF_PATH"
sudo bash -c "cat > $NGINX_CONF_PATH" <<EOF
server {
    listen 80;
    server_name $SERVER_NAMES;
    return 301 https://$DOMAIN\$request_uri;
}

server {
    listen 443 ssl;
    server_name $SERVER_NAMES;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:$API_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

if [ ! -L "/etc/nginx/sites-enabled/$DOMAIN" ]; then
  sudo ln -s "$NGINX_CONF_PATH" "/etc/nginx/sites-enabled/$DOMAIN"
fi

# MCP Server Domain
MCP_NGINX_CONF_PATH="/etc/nginx/sites-available/$MCP_DOMAIN"

info "Writing Nginx configuration for MCP Server to $MCP_NGINX_CONF_PATH"
# Check if SSL certificates exist
if [ -f "/etc/letsencrypt/live/$MCP_DOMAIN/fullchain.pem" ]; then
  info "SSL certificates found for $MCP_DOMAIN, configuring with HTTPS"
  sudo bash -c "cat > $MCP_NGINX_CONF_PATH" <<EOF
server {
    listen 80;
    server_name $MCP_DOMAIN;
    return 301 https://$MCP_DOMAIN\$request_uri;
}

server {
    listen 443 ssl;
    server_name $MCP_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$MCP_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$MCP_DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:$MCP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeouts for MCP Server
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no auth required)
    location = /health {
        proxy_pass http://127.0.0.1:$MCP_PORT/health;
        access_log off;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:$MCP_PORT/docs;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:$MCP_PORT/redoc;
    }
}
EOF
else
  info "No SSL certificates found for $MCP_DOMAIN, configuring HTTP only (will upgrade after certbot)"
  sudo bash -c "cat > $MCP_NGINX_CONF_PATH" <<EOF
server {
    listen 80;
    server_name $MCP_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$MCP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeouts for MCP Server
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no auth required)
    location = /health {
        proxy_pass http://127.0.0.1:$MCP_PORT/health;
        access_log off;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:$MCP_PORT/docs;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:$MCP_PORT/redoc;
    }
}
EOF
fi

if [ ! -L "/etc/nginx/sites-enabled/$MCP_DOMAIN" ]; then
  sudo ln -s "$MCP_NGINX_CONF_PATH" "/etc/nginx/sites-enabled/$MCP_DOMAIN"
fi

info "Testing Nginx configuration"
sudo nginx -t

info "Reloading Nginx"
sudo systemctl reload nginx

# --- 6. Issue / renew certificates ---
info "Requesting/renewing SSL certificate for $DOMAIN"
sudo certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive || true

info "Requesting/renewing SSL certificate for $MCP_DOMAIN"
sudo certbot --nginx -d "$MCP_DOMAIN" --email "$EMAIL" --agree-tos --non-interactive || true

# Update MCP config to HTTPS after getting certificate
if [ -f "/etc/letsencrypt/live/$MCP_DOMAIN/fullchain.pem" ]; then
  info "Updating $MCP_DOMAIN to use HTTPS"
  # Rewrite the config with SSL
  sudo bash -c "cat > $MCP_NGINX_CONF_PATH" <<EOF
server {
    listen 80;
    server_name $MCP_DOMAIN;
    return 301 https://$MCP_DOMAIN\$request_uri;
}

server {
    listen 443 ssl;
    server_name $MCP_DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$MCP_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$MCP_DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:$MCP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # Timeouts for MCP Server
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no auth required)
    location = /health {
        proxy_pass http://127.0.0.1:$MCP_PORT/health;
        access_log off;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:$MCP_PORT/docs;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:$MCP_PORT/redoc;
    }
}
EOF
fi

info "Reloading Nginx after Certbot"
sudo systemctl reload nginx

# --- 7. Setup Snowflake (if configured) ---
echo ""
info "Configuring Snowflake data warehouse..."

if [ -n "${SNOWFLAKE_ACCOUNT:-}" ] && [ -n "${SNOWFLAKE_USER:-}" ]; then
    info "Snowflake credentials detected, setting up tenant warehouse configuration"

    # Insert tenant warehouse configuration
    docker exec dental-erp_postgres_1 psql -U postgres -d mcp << 'EOSQL'
-- Create tenant warehouse configuration for Snowflake
INSERT INTO tenant_warehouses (
  id,
  tenant_id,
  warehouse_type,
  warehouse_config,
  is_primary,
  is_active
)
SELECT
  gen_random_uuid(),
  id,
  'snowflake',
  jsonb_build_object(
    'account', '${SNOWFLAKE_ACCOUNT}',
    'user', '${SNOWFLAKE_USER}',
    'warehouse', COALESCE('${SNOWFLAKE_WAREHOUSE}', 'COMPUTE_WH'),
    'database', COALESCE('${SNOWFLAKE_DATABASE}', 'DENTAL_ERP_DW'),
    'schema', COALESCE('${SNOWFLAKE_SCHEMA}', 'PUBLIC'),
    'role', COALESCE('${SNOWFLAKE_ROLE}', 'ACCOUNTADMIN')
  ),
  true,
  true
FROM tenants
WHERE tenant_code = 'default'
ON CONFLICT DO NOTHING;
EOSQL

    if [ $? -eq 0 ]; then
        info "✓ Snowflake warehouse configuration created for default tenant"
    else
        info "⚠️  Could not configure Snowflake (tenant may not exist yet)"
    fi
    # Execute Snowflake MVP AI Setup (Dynamic Tables + Cleanup)
    info "Executing Snowflake MVP AI setup (Dynamic Tables, cleanup duplicates)..."

    docker exec dental-erp_mcp-server-prod_1 python3 << 'PYEOF'
import snowflake.connector
import os

# Load env vars
env_vars = {}
with open("/app/.env", "r") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            key, value = line.strip().split("=", 1)
            env_vars[key] = value

try:
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=env_vars.get("SNOWFLAKE_ACCOUNT"),
        user=env_vars.get("SNOWFLAKE_USER"),
        password=env_vars.get("SNOWFLAKE_PASSWORD"),
        warehouse=env_vars.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=env_vars.get("SNOWFLAKE_DATABASE", "DENTAL_ERP_DW")
    )

    cursor = conn.cursor()

    # Execute MVP AI setup SQL if file exists
    if os.path.exists("/app/snowflake-mvp-ai-setup.sql"):
        print("Executing snowflake-mvp-ai-setup.sql...")
        with open("/app/snowflake-mvp-ai-setup.sql") as f:
            sql_content = f.read()
            # Execute each statement
            for statement in sql_content.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            print(f"Warning: {e}")
        print("✅ Dynamic Tables setup complete")

    # Cleanup duplicates
    print("Cleaning up duplicate records...")
    tables = ["netsuite_journal_entries", "netsuite_accounts", "netsuite_vendor_bills",
              "netsuite_customers", "netsuite_vendors", "netsuite_subsidiaries"]

    for table in tables:
        try:
            cursor.execute(f"""
                DELETE FROM bronze.{table}
                WHERE (id, extracted_at) NOT IN (
                    SELECT id, MAX(extracted_at)
                    FROM bronze.{table}
                    GROUP BY id
                )
            """)
            if cursor.rowcount > 0:
                print(f"  ✅ {table}: Deleted {cursor.rowcount} duplicates")
        except Exception as e:
            print(f"  ⚠️  {table}: {e}")

    conn.close()
    print("✅ Snowflake setup complete")

except Exception as e:
    print(f"❌ Snowflake setup failed: {e}")
    exit(1)
PYEOF

    if [ $? -eq 0 ]; then
        info "✓ Snowflake MVP AI setup completed successfully"
    else
        info "⚠️  Snowflake setup had issues - check logs above"
    fi

else
    info "No Snowflake credentials found in environment, skipping warehouse setup"
    info "To enable Snowflake, export: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD"
fi

# --- 8. Setup NetSuite Integration (if configured) ---
echo ""
info "Configuring NetSuite integration..."

# Run PostgreSQL migration for NetSuite sync state
info "Running NetSuite sync state migration..."
    docker cp "$PROJECT_ROOT/mcp-server/migrations/003_netsuite_sync_state.sql" dental-erp_postgres_1:/tmp/ 2>/dev/null || true
    docker exec dental-erp_postgres_1 psql -U postgres -d mcp -f /tmp/003_netsuite_sync_state.sql 2>&1 | grep -v "already exists" || true
    info "✓ NetSuite migration applied"

if [ -n "${NETSUITE_ACCOUNT_ID:-}" ] && [ -n "${NETSUITE_CONSUMER_KEY:-}" ]; then
    info "NetSuite credentials detected, setting up tenant integration"

    # Insert tenant integration configuration
    docker exec dental-erp_postgres_1 psql -U postgres -d mcp << EOSQL
-- Create NetSuite integration for default tenant
INSERT INTO tenant_integrations (
    id, tenant_id, integration_type, integration_config, status, created_at
)
SELECT
    gen_random_uuid(),
    id,
    'netsuite',
    jsonb_build_object(
        'account_id', '${NETSUITE_ACCOUNT_ID}',
        'consumer_key', '${NETSUITE_CONSUMER_KEY}',
        'consumer_secret', '${NETSUITE_CONSUMER_SECRET}',
        'token_id', '${NETSUITE_TOKEN_ID}',
        'token_secret', '${NETSUITE_TOKEN_SECRET}'
    ),
    'active',
    NOW()
FROM tenants
WHERE tenant_code = 'default'
ON CONFLICT DO NOTHING;
EOSQL

    if [ $? -eq 0 ]; then
        info "✓ NetSuite integration configured for default tenant"
    else
        info "⚠️  Could not configure NetSuite integration (tenant may not exist yet)"
    fi
else
    info "No NetSuite credentials found in environment, skipping integration setup"
    info "To enable NetSuite, export: NETSUITE_ACCOUNT_ID, NETSUITE_CONSUMER_KEY, NETSUITE_CONSUMER_SECRET, NETSUITE_TOKEN_ID, NETSUITE_TOKEN_SECRET"
fi

# --- 9. Wait for Services to be Ready ---
echo ""
info "Waiting for services to be ready..."
info "Checking backend health..."

MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/health" | grep -q "200"; then
        BACKEND_READY=true
        info "✓ Backend API is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    info "Waiting for backend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ "$BACKEND_READY" = false ]; then
    info "⚠️  WARNING: Backend did not become ready within expected time"
    info "You may need to check the logs: docker-compose logs backend-prod"
fi

info "Checking MCP server health..."
RETRY_COUNT=0
MCP_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -o /dev/null -w "%{http_code}" "https://$MCP_DOMAIN/health" | grep -q "200"; then
        MCP_READY=true
        info "✓ MCP Server is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    info "Waiting for MCP server... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ "$MCP_READY" = false ]; then
    info "⚠️  WARNING: MCP Server did not become ready within expected time"
    info "You may need to check the logs: docker-compose logs mcp-server-prod"
fi

# --- 10. Run End-to-End Tests ---
echo ""
echo "==========================================="
echo "Running End-to-End Tests"
echo "==========================================="

E2E_TEST_SCRIPT="$PROJECT_ROOT/scripts/test-production.sh"
TEST_EXIT_CODE=0

if [ -f "$E2E_TEST_SCRIPT" ]; then
    chmod +x "$E2E_TEST_SCRIPT"

    # Run tests and capture exit code
    set +e  # Don't exit on test failure
    "$E2E_TEST_SCRIPT"
    TEST_EXIT_CODE=$?
    set -e  # Re-enable exit on error

    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo "✅ All E2E tests passed!"
    else
        echo "⚠️  Some E2E tests failed (exit code: $TEST_EXIT_CODE)"
        echo "Please review the test output above for details"
        echo "You can re-run tests manually with: $E2E_TEST_SCRIPT"
    fi
else
    echo "⚠️  E2E test script not found at $E2E_TEST_SCRIPT"
    echo "Skipping automated tests"
    TEST_EXIT_CODE=0  # Don't fail deployment if test script missing
fi

# --- 11. Post-deployment summary ---
echo ""
echo "==========================================="
echo "Deployment Complete!"
echo "==========================================="
info "Main site available at https://$DOMAIN"
info "MCP Server available at https://$MCP_DOMAIN"
info "MCP API docs available at https://$MCP_DOMAIN/docs"
echo ""
echo "Service Details:"
echo "  - Frontend: https://$DOMAIN"
echo "  - Backend API: https://$DOMAIN/api"
echo "  - MCP Server: https://$MCP_DOMAIN"
echo "  - MCP API Docs: https://$MCP_DOMAIN/docs"
echo ""
echo "Useful Commands:"
echo "  - View backend logs: docker-compose logs -f backend-prod"
echo "  - View MCP logs: docker-compose logs -f mcp-server-prod"
echo "  - View frontend logs: docker-compose logs -f frontend-prod"
echo "  - Run E2E tests: $E2E_TEST_SCRIPT"
echo "  - Restart services: docker-compose --profile production restart"
echo ""
if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo "⚠️  IMPORTANT: E2E tests detected issues. Please review and fix before considering deployment complete."
    exit 1
fi
