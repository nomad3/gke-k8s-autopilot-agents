# Backup Strategy for GKE Autopilot

This document outlines the backup and recovery strategy for the GKE Autopilot cluster and its stateful workloads.

## 1. Infrastructure Backup (Terraform)

The entire infrastructure is defined as code (IaC) using Terraform.
- **State Backup**: Terraform state is stored in a GCS bucket with versioning enabled.
- **Recovery**: Re-run `terraform apply` to recreate infrastructure components.

## 2. Application Configuration Backup (GitOps)

All Kubernetes manifests and Helm charts are stored in Git.
- **Source of Truth**: The Git repository is the single source of truth.
- **Recovery**: Re-deploy applications using Helm or CI/CD pipelines.

## 3. Stateful Workload Backup (Backup for GKE)

We use **Backup for GKE**, a fully managed service for backing up and restoring GKE workloads.

### Setup

1. **Enable Backup for GKE API**:
   ```bash
   gcloud services enable gkebackup.googleapis.com
   ```

2. **Create Backup Plan**:
   ```bash
   gcloud beta container backup-restore backup-plans create daily-backup \
       --project=PROJECT_ID \
       --location=us-central1 \
       --cluster=projects/PROJECT_ID/locations/us-central1/clusters/gke-autopilot-cluster \
       --all-namespaces \
       --include-secrets \
       --include-volume-data \
       --cron-schedule="0 3 * * *" \
       --retain-days=30
   ```

### Restore Process

1. **List Backups**:
   ```bash
   gcloud beta container backup-restore backups list \
       --project=PROJECT_ID \
       --location=us-central1 \
       --backup-plan=daily-backup
   ```

2. **Restore**:
   ```bash
   gcloud beta container backup-restore restores create restore-job-1 \
       --project=PROJECT_ID \
       --location=us-central1 \
       --backup=projects/PROJECT_ID/locations/us-central1/backupPlans/daily-backup/backups/BACKUP_NAME \
       --cluster=projects/PROJECT_ID/locations/us-central1/clusters/gke-autopilot-cluster
   ```

## 4. Database Backup (PostgreSQL)

For the self-managed PostgreSQL (StatefulSet), we use a sidecar or cronjob approach, or migrate to Cloud SQL (recommended).

### Option A: Cloud SQL (Recommended)
- **Automated Backups**: Enabled by default (7 days retention).
- **Point-in-Time Recovery**: Enabled.

### Option B: Self-Managed (Current)
We implement a Kubernetes CronJob to dump the database to GCS.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: database
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: dev-database-sa
          containers:
          - name: backup
            image: google/cloud-sdk:alpine
            command: ["/bin/sh", "-c"]
            args:
            - |
              pg_dump -h postgres-service -U postgres app_db > /tmp/backup.sql
              gsutil cp /tmp/backup.sql gs://PROJECT-backups/postgres/$(date +%Y%m%d).sql
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          restartPolicy: OnFailure
```

## 5. Secret Backup

Secrets are stored in **Google Secret Manager**.
- **Versioning**: Enabled automatically.
- **Recovery**: Access previous versions via Secret Manager UI or API.

## 6. Disaster Recovery (DR) Scenarios

| Scenario | Recovery Action | RTO (Target) | RPO (Target) |
|----------|-----------------|--------------|--------------|
| **Pod Failure** | Automatic restart by K8s | < 1 min | 0 |
| **Node Failure** | Automatic repair by GKE | < 5 min | 0 |
| **Zone Failure** | Traffic shifts to other zones (Regional Cluster) | < 1 min | 0 |
| **Region Failure** | Deploy to new region using Terraform + GitOps | 4 hours | 24 hours (Backup freq) |
| **Accidental Deletion** | Restore from Backup for GKE | 1 hour | 24 hours |
| **Database Corruption** | Restore from DB Backup / PITR | 1 hour | 5 min (Cloud SQL) |

## 7. Testing Backups

- **Frequency**: Test restoration quarterly.
- **Procedure**:
  1. Create a temporary namespace.
  2. Restore workload to temp namespace.
  3. Verify data integrity.
  4. Delete temp namespace.
