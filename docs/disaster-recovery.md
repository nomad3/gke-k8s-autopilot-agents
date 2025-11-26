# Disaster Recovery (DR) Procedures

This runbook details the procedures for recovering from major failures in the GKE environment.

## 1. Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| DevOps Lead | Jane Doe | +1-555-0100 |
| Database Admin | John Smith | +1-555-0101 |
| Cloud Support | Google Cloud | Console Support |

## 2. Severity Levels

- **Sev-1 (Critical)**: Production down, data loss risk. Immediate response required (24/7).
- **Sev-2 (High)**: Performance degraded, non-critical feature broken. Response within 2 hours.
- **Sev-3 (Medium)**: Minor issue, workaround available. Response next business day.

## 3. Recovery Procedures

### Scenario A: Accidental Namespace Deletion

**Symptoms**: Application unreachable, `kubectl get ns` shows missing namespace.

**Recovery Steps**:
1. **Verify Deletion**: Confirm namespace is gone.
2. **Locate Backup**: Find latest successful backup in Backup for GKE.
   ```bash
   gcloud beta container backup-restore backups list --backup-plan=daily-backup
   ```
3. **Restore Namespace**:
   ```bash
   gcloud beta container backup-restore restores create restore-ns-$(date +%s) \
       --backup=BACKUP_PATH \
       --cluster=CLUSTER_PATH \
       --selected-namespaces=target-namespace
   ```
4. **Verify Restore**: Check pods and services are running.
5. **Update DNS**: If LoadBalancer IP changed, update DNS records.

### Scenario B: Region Failure (Total Site Outage)

**Symptoms**: GKE cluster unreachable in primary region (us-central1).

**Recovery Steps**:
1. **Declare Disaster**: Notify stakeholders.
2. **Update Terraform**: Change region variable in `terraform.tfvars`.
   ```hcl
   region = "us-east1"
   ```
3. **Deploy Infrastructure**:
   ```bash
   terraform apply -var-file="terraform-prod.tfvars"
   ```
4. **Restore Data**:
   - **Database**: Restore Cloud SQL / Postgres backup to new region.
   - **Secrets**: Re-populate Secret Manager in new region (if not global).
5. **Deploy Applications**:
   ```bash
   # Update kubeconfig
   gcloud container clusters get-credentials gke-autopilot-cluster-prod --region us-east1
   
   # Trigger CI/CD or manual Helm deploy
   helm upgrade --install backend ...
   ```
6. **Update DNS**: Point domain to new Load Balancer IP.

### Scenario C: Database Corruption

**Symptoms**: Application errors, data inconsistencies.

**Recovery Steps**:
1. **Stop Writes**: Scale down backend services to 0.
   ```bash
   kubectl scale deployment backend --replicas=0 -n backend
   ```
2. **Identify Restore Point**: Determine time of corruption.
3. **Restore Database**:
   - **Cloud SQL**: Perform Point-in-Time Recovery (PITR).
   - **Self-Managed**: Restore from latest SQL dump.
     ```bash
     cat backup.sql | kubectl exec -i postgres-pod -- psql -U postgres app_db
     ```
4. **Verify Data**: Check critical tables.
5. **Resume Services**: Scale backend services back up.
   ```bash
   kubectl scale deployment backend --replicas=3 -n backend
   ```

### Scenario D: Bad Deployment (Rollback)

**Symptoms**: High error rate after deployment.

**Recovery Steps**:
1. **Identify Issue**: Check logs and metrics.
2. **Rollback Helm Release**:
   ```bash
   helm rollback backend -n backend
   ```
3. **Verify Stability**: Monitor error rates for 10 minutes.
4. **Investigate Root Cause**: Analyze logs of failed version.

## 4. Post-Incident Review (PIR)

After any Sev-1 or Sev-2 incident:
1. Create Incident Report.
2. Analyze Root Cause (5 Whys).
3. Identify Action Items to prevent recurrence.
4. Update DR procedures if gaps were found.
