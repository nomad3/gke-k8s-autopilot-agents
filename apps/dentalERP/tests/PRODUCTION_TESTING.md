# Production Testing Guide

This guide explains how to test the DentalERP system in production to ensure all critical components and flows are working correctly.

## Overview

We have three comprehensive production test suites:

1. **`test-production.sh`** - Full system test (all components)
2. **`test-production-critical-flows.sh`** - End-to-end critical user flows
3. **`test-production-connectors.sh`** - External system connectors and integrations

## Prerequisites

### Required Environment Variables

```bash
# MCP Server API Key (required for all tests)
export MCP_API_KEY="your-production-mcp-api-key"

# Backend authentication token (optional, for backend tests)
export BACKEND_TOKEN="your-jwt-token"

# Test user credentials (optional, for auth flow tests)
export TEST_EMAIL="test@dentalerp.demo"
export TEST_PASSWORD="your-test-password"

# Tenant ID for multi-tenant tests (optional, defaults to "default")
export TENANT_ID="default"
```

### Getting Your API Keys

#### MCP API Key
1. Log into production MCP server
2. Navigate to API Keys management
3. Create a new API key or use existing one
4. Copy the key value

#### Backend Token
1. Log into production frontend at https://dentalerp.agentprovision.com
2. Open browser DevTools → Network tab
3. Look for any `/api` request
4. Copy the `Authorization: Bearer <token>` header value

## Test Suite 1: Full System Test

Tests all production components and endpoints.

### What It Tests

- ✅ Frontend accessibility (homepage, login page)
- ✅ Backend API health and endpoints
- ✅ MCP Server health and API
- ✅ Analytics endpoints (production summary, daily, by-practice)
- ✅ Warehouse connectivity (via analytics queries)
- ✅ PDF ingestion endpoints
- ✅ dbt operation endpoints
- ✅ CORS and security headers
- ✅ Frontend-MCP direct integration

### Running the Test

```bash
# Basic run (some tests will be skipped without credentials)
./scripts/test-production.sh

# Full run with all credentials
export MCP_API_KEY="your-key"
export BACKEND_TOKEN="your-token"
./scripts/test-production.sh
```

### Expected Output

```
================================================================================
DentalERP Production Test Suite
================================================================================

Testing production environment:
  Frontend: https://dentalerp.agentprovision.com
  Backend:  https://dentalerp.agentprovision.com/api
  MCP:      https://mcp.agentprovision.com

================================================================================
TEST SUITE 1: Frontend Accessibility
================================================================================
▶ TEST 1: Frontend Homepage
✅ PASS: Frontend is accessible at https://dentalerp.agentprovision.com

[... more tests ...]

================================================================================
TEST SUMMARY
================================================================================

Total Tests:  27
Passed:       25
Failed:       2

✅ ALL PRODUCTION TESTS PASSED
```

## Test Suite 2: Critical Flows Test

Tests end-to-end user flows that are critical to the application.

### What It Tests

- 🔐 User authentication and session management
- 📊 Dashboard data loading (executive view)
- 📄 PDF upload → AI extraction → dbt → analytics query pipeline
- 🏢 Multi-tenant data isolation
- ⚠️ Error handling and recovery
- ⚡ Performance and response times

### Running the Test

```bash
# Run critical flows
export MCP_API_KEY="your-key"
export TEST_EMAIL="test@dentalerp.demo"
export TEST_PASSWORD="your-password"
./scripts/test-production-critical-flows.sh
```

### Expected Output

```
================================================================================
DentalERP Production Critical Flows Test
================================================================================

Testing environment: PRODUCTION

================================================================================
CRITICAL FLOW 1: User Authentication & Session Management
================================================================================
  Step 1: Logging in with credentials
  Step 2: Login successful
  Step 3: Testing authenticated request
  Step 4: Authenticated request successful
  Step 5: Testing token refresh
  Step 6: Token refresh successful
✅ FLOW PASSED: User Authentication

[... more flows ...]

================================================================================
CRITICAL FLOWS TEST SUMMARY
================================================================================

Total Flows:  6
Passed:       6
Failed:       0

✅ ALL CRITICAL FLOWS PASSED
```

## Test Suite 3: Connectors Test

Tests all external system connectors and integrations.

### What It Tests

- 🗄️ Snowflake data warehouse connection
- 🔌 Tenant integrations status
- ⚙️ Warehouse configuration
- 📦 Products and capabilities
- 📋 Available integrations registry
- ✔️ Data quality checks

### Running the Test

```bash
# Run connector tests
export MCP_API_KEY="your-key"
export TENANT_ID="default"  # or your tenant code
./scripts/test-production-connectors.sh
```

### Expected Output

```
================================================================================
DentalERP Production Connector Tests
================================================================================

Testing connectors for tenant: default
MCP Server: https://mcp.agentprovision.com

================================================================================
CONNECTOR TEST 1: Snowflake Data Warehouse
================================================================================
  → Testing Snowflake connectivity via analytics query
  → Snowflake query successful
  → Data retrieved from warehouse
✅ CONNECTOR OK: Snowflake

[... more connectors ...]

================================================================================
CONNECTOR TEST SUMMARY
================================================================================

Total Connectors: 6
Passed:           6
Failed:           0

✅ ALL CONNECTOR TESTS PASSED
```

## Running All Tests in CI/CD

You can run all three test suites sequentially in your CI/CD pipeline:

```bash
#!/bin/bash
# ci-production-tests.sh

set -e

echo "Running production test suites..."

# Test 1: Full system
echo "=== Running full system test ==="
./scripts/test-production.sh

# Test 2: Critical flows
echo "=== Running critical flows test ==="
./scripts/test-production-critical-flows.sh

# Test 3: Connectors
echo "=== Running connector tests ==="
./scripts/test-production-connectors.sh

echo "✅ All production tests passed!"
```

### GitHub Actions Example

```yaml
name: Production Tests

on:
  schedule:
    - cron: '0 */6 * * *'  # Run every 6 hours
  workflow_dispatch:  # Allow manual trigger

jobs:
  production-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Full System Test
        env:
          MCP_API_KEY: ${{ secrets.PROD_MCP_API_KEY }}
          BACKEND_TOKEN: ${{ secrets.PROD_BACKEND_TOKEN }}
        run: ./scripts/test-production.sh

      - name: Run Critical Flows Test
        env:
          MCP_API_KEY: ${{ secrets.PROD_MCP_API_KEY }}
          TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: ./scripts/test-production-critical-flows.sh

      - name: Run Connector Tests
        env:
          MCP_API_KEY: ${{ secrets.PROD_MCP_API_KEY }}
          TENANT_ID: default
        run: ./scripts/test-production-connectors.sh
```

## Troubleshooting

### Test Failures

#### "MCP_API_KEY not set"
- Export your MCP API key before running tests
- Check that the key is valid and not expired

#### "404 on analytics endpoints"
- Verify MCP server is running at https://mcp.agentprovision.com
- Check that Snowflake credentials are configured
- Verify tenant has warehouse configured

#### "Authentication failed"
- Verify test user exists in production database
- Check password is correct
- Ensure user has proper role/permissions

#### "Snowflake connection failed"
- Check Snowflake credentials in MCP server environment
- Verify warehouse is running and not suspended
- Check network connectivity from production to Snowflake

#### "Performance test failed (response too slow)"
- Check Snowflake warehouse size
- Verify no ongoing heavy queries
- Consider scaling up warehouse temporarily

### Common Issues

#### CORS Errors
If you see CORS errors in the browser but tests pass:
- Tests use server-side requests (no CORS)
- Browser may need different CORS config
- Check nginx/load balancer CORS headers

#### SSL Certificate Issues
```bash
# Temporarily disable SSL verification for testing (NOT recommended for production)
export CURL_CA_BUNDLE=""
curl -k https://...
```

#### Timeout Issues
```bash
# Increase curl timeout in test scripts
# Edit the script and change timeout values
timeout: 30000  # 30 seconds
```

## Best Practices

### Regular Testing Schedule

1. **After Each Deployment** - Run full system test
2. **Daily** - Run critical flows test
3. **Weekly** - Run full connector tests
4. **Monthly** - Manual smoke test with real user

### Monitoring Integration

Integrate test results with monitoring:

```bash
# Send results to monitoring system
./scripts/test-production.sh && \
  curl -X POST https://monitoring.example.com/api/metrics \
    -d '{"test":"production","status":"passed","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
```

### Alerting

Set up alerts for test failures:

```bash
#!/bin/bash
if ! ./scripts/test-production.sh; then
  # Send alert to Slack/PagerDuty/Email
  curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
    -d '{"text":"🚨 Production tests failed!"}'
  exit 1
fi
```

## Additional Resources

- [Architecture Overview](../CLAUDE.md)
- [Local Development Testing](./DOCKER_E2E_TEST_GUIDE.md)
- [PDF Ingestion Testing](./PDF_INGESTION_GUIDE.md)
- [Snowflake Integration](./SNOWFLAKE_FRONTEND_INTEGRATION.md)

## Support

If you encounter issues not covered in this guide:
1. Check application logs (MCP server, backend)
2. Review recent deployment changes
3. Contact the DevOps team
4. Open an issue in the repository

---

**Last Updated**: December 2024
**Maintained By**: DentalERP DevOps Team
