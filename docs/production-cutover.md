# Production Cutover Plan

This document outlines the steps to migrate production traffic to the new GKE Autopilot cluster.

## Pre-Requisites

- [ ] **Infrastructure Ready**: GKE Prod cluster deployed and green (Terraform applied).
- [ ] **Applications Deployed**: All microservices deployed to Prod namespace (Helm).
- [ ] **Data Migrated**: Database data synced to Prod DB (Cloud SQL or StatefulSet).
- [ ] **Testing Complete**: Integration and Load tests passed in Staging/Prod.
- [ ] **DNS Access**: Access to DNS provider (e.g., Cloud DNS, GoDaddy).
- [ ] **TTL Lowered**: DNS TTL lowered to 60s (24h in advance).

## Cutover Timeline (T-Minus)

### T-24 Hours: Preparation
1. **Lower DNS TTL**: Set TTL for `api.yourdomain.com` and `www.yourdomain.com` to 60 seconds.
2. **Freeze Code**: No new commits to `main` branch.
3. **Data Sync**: Perform initial data sync (if using external DB migration tool).

### T-1 Hour: Final Checks
1. **Verify Health**: Check GKE dashboards (CPU, Memory, Error Rates).
2. **Smoke Test**: Run manual smoke tests against GKE Ingress IP directly.
   ```bash
   curl -k https://<GKE_INGRESS_IP>/health
   ```
3. **Team Standby**: Ensure DevOps and Dev leads are online.

### T-0: The Cutover
1. **Maintenance Mode**: Enable maintenance page on old infrastructure (optional but recommended).
2. **Stop Writes**: Stop writes to old database (read-only mode).
3. **Final Data Sync**: Sync remaining data delta to new DB.
4. **Verify Data**: Confirm row counts match between old and new DB.
5. **Update DNS**: Change A records to point to GKE Ingress IP.
   - `api.yourdomain.com` -> `34.x.x.x`
   - `www.yourdomain.com` -> `34.x.x.x`
6. **Flush DNS**: `ipconfig /flushdns` (local), wait for propagation.

### T+15 Minutes: Validation
1. **Traffic Monitoring**: Watch GKE Ingress traffic metrics.
2. **Error Rates**: Monitor 5xx errors in Cloud Monitoring.
3. **User Verification**: Perform login and critical flows on production domain.

### T+1 Hour: Stabilization
1. **Scale Check**: Verify HPA is scaling pods if load increases.
2. **Logs Review**: Check application logs for unexpected errors.

### T+24 Hours: Cleanup
1. **Raise DNS TTL**: Set TTL back to standard (e.g., 1 hour).
2. **Decommission Old Infra**: Schedule shutdown of old Docker Compose servers.

## Rollback Plan (Abort Criteria)

**Triggers**:
- Error rate > 1% for 5 minutes.
- Critical login/payment failure.
- Data corruption detected.

**Steps**:
1. **Revert DNS**: Point A records back to old infrastructure IP.
2. **Resume Old DB**: Re-enable writes on old database.
   - *Note*: Data written to new DB during cutover may need manual back-porting.
3. **Notify Users**: Post status update about maintenance extension.
4. **Investigate**: Analyze logs to determine root cause before retrying.
