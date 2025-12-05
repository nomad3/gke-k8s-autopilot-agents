#!/bin/bash

# MCP Refactor Verification Script
# Verifies that the MCP migration is complete and working

set -e

echo "🔍 MCP Refactor Verification Script"
echo "===================================="
echo ""

ERRORS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: MCP Client exists
echo "✓ Checking MCP Client exists..."
if [ -f "src/services/mcpClient.ts" ]; then
    echo -e "${GREEN}  ✓ MCP Client found${NC}"
else
    echo -e "${RED}  ✗ MCP Client not found${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: Old integration files removed
echo "✓ Checking old integration files removed..."
OLD_FILES=(
    "src/services/integrationHub/connectors/adpConnector.ts"
    "src/services/integrationHub/connectors/netsuiteConnector.ts"
    "src/services/integrationHub/hub.ts"
    "src/services/integrationHub/credentialsService.ts"
    "src/services/snowflake.ts"
    "src/utils/crypto.ts"
)

for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${RED}  ✗ Old file still exists: $file${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}  ✓ All old integration files removed${NC}"
fi

# Check 3: Environment configuration updated
echo "✓ Checking environment configuration..."
if grep -q "MCP_API_URL" .env.example 2>/dev/null; then
    echo -e "${GREEN}  ✓ .env.example has MCP configuration${NC}"
else
    echo -e "${RED}  ✗ .env.example missing MCP configuration${NC}"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "mcp:" src/config/environment.ts; then
    echo -e "${GREEN}  ✓ environment.ts has MCP config${NC}"
else
    echo -e "${RED}  ✗ environment.ts missing MCP config${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 4: TypeScript compilation
echo "✓ Running TypeScript type check..."
if npm run type-check > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Type check passed${NC}"
else
    echo -e "${RED}  ✗ Type check failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: Build succeeds
echo "✓ Running build..."
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Build succeeded${NC}"
else
    echo -e "${RED}  ✗ Build failed${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: No references to old integration hub
echo "✓ Checking for old integration references..."
if grep -r "integrationHub" src/ 2>/dev/null | grep -v "node_modules" | grep -q .; then
    echo -e "${YELLOW}  ⚠ Found references to old integrationHub${NC}"
    grep -r "integrationHub" src/ | grep -v "node_modules" | head -5
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✓ No old integration references found${NC}"
fi

# Check 7: Package.json updated
echo "✓ Checking package.json..."
if grep -q "snowflake-sdk" package.json; then
    echo -e "${RED}  ✗ snowflake-sdk still in dependencies${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}  ✓ Unnecessary dependencies removed${NC}"
fi

# Check 8: Documentation exists
echo "✓ Checking documentation..."
DOCS=(
    "MCP_MIGRATION.md"
    ".env.example"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}  ✓ $doc exists${NC}"
    else
        echo -e "${RED}  ✗ $doc missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# Summary
echo ""
echo "===================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! MCP refactor is complete.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy MCP Server to production"
    echo "2. Update production .env with MCP credentials"
    echo "3. Deploy this updated ERP backend"
    echo "4. Monitor MCP connectivity"
    exit 0
else
    echo -e "${RED}❌ $ERRORS check(s) failed. Please review above.${NC}"
    exit 1
fi
