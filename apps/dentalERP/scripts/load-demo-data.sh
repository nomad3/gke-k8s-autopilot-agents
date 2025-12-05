#!/bin/bash
#=============================================================================
# Load Demo Transaction Data to Snowflake
# Loads 37,759 real NetSuite transactions from CSV backups
#=============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backup"

info() { echo "[load-demo] $1"; }
error() { echo "[load-demo] ERROR: $1" >&2; }

# Check prerequisites
if [ ! -f "$BACKUP_DIR/TransactionDetail_eastlake_mapped.csv" ]; then
    error "Transaction CSV files not found in $BACKUP_DIR"
    exit 1
fi

# Verify Snowflake environment variables
REQUIRED_VARS=(
    SNOWFLAKE_ACCOUNT
    SNOWFLAKE_USER
    SNOWFLAKE_PASSWORD
    SNOWFLAKE_DATABASE
    SNOWFLAKE_WAREHOUSE
)

missing_vars=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    error "Missing required environment variables: ${missing_vars[*]}"
    error "Source your .env file or export these variables"
    exit 1
fi

info "Starting data ingestion..."
info "  Eastlake: $(wc -l < "$BACKUP_DIR/TransactionDetail_eastlake_mapped.csv") rows"
info "  Torrey Pines: $(wc -l < "$BACKUP_DIR/TransactionDetail_torrey_pines_mapped.csv") rows"
info "  ADS: $(wc -l < "$BACKUP_DIR/TransactionDetail_ads_mapped.csv") rows"

# Run Python ingestion script
info "Running Python ingestion script..."
python3 "$SCRIPT_DIR/ingest-netsuite-multi-practice.py"

if [ $? -eq 0 ]; then
    info "✓ Data loaded successfully!"
    info "Next steps:"
    info "  1. Verify Bronze layer: SELECT COUNT(*) FROM bronze.netsuite_journal_entries;"
    info "  2. Check dynamic tables: SHOW DYNAMIC TABLES IN SCHEMA silver;"
    info "  3. Test analytics: SELECT * FROM gold.daily_financial_summary LIMIT 10;"
else
    error "Data loading failed"
    exit 1
fi
