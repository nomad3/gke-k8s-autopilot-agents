-- Track sync state for each NetSuite record type per tenant
CREATE TABLE IF NOT EXISTS netsuite_sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    record_type VARCHAR(50) NOT NULL,
    last_sync_timestamp TIMESTAMP,
    last_sync_status VARCHAR(20) DEFAULT 'pending',
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, record_type)
);

CREATE INDEX idx_netsuite_sync_tenant ON netsuite_sync_state(tenant_id);
CREATE INDEX idx_netsuite_sync_next_retry ON netsuite_sync_state(next_retry_at)
    WHERE last_sync_status = 'failed';
CREATE INDEX idx_netsuite_sync_record_type ON netsuite_sync_state(record_type);

COMMENT ON TABLE netsuite_sync_state IS 'Tracks NetSuite sync state for incremental syncs';
