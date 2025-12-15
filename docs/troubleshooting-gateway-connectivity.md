# Troubleshooting Gateway Connectivity & "No Healthy Upstream" Errors

This guide documents the resolution of "no healthy upstream" errors and related connectivity issues encountered during the migration to Gateway API and GKE Autopilot.

## Symptom
The frontend application (`https://scdp-front-prod.agentprovision.com/`) displays a `503 Service Unavailable` or `no healthy upstream` error.

## Root Causes & Solutions

### 1. Gateway HTTPRoute Misconfiguration
**Issue:** The `HTTPRoute` resource was referencing a backend service name that did not exist or was incorrect.
- **Error:** `services backend/backend not found`
- **Cause:** `helm/values/backend-prod.yaml` referenced `backend` instead of `backend-microservice`.
- **Fix:** Update `backendRefs` in the `HTTPRoute` configuration to point to the correct Service name.

```yaml
backendRefs:
  - name: backend-microservice
    port: 80
```

### 2. Backend Database Connectivity (Cloud SQL)
The backend pods were failing health checks because they could not connect to the Cloud SQL instance. This caused the Gateway to mark them as unhealthy.

#### A. Pod Security Standards (PSS) Violation
**Issue:** The `cloud-sql-proxy` sidecar container failed to start due to GKE Autopilot's restricted Pod Security Standards.
- **Error:** `violates PodSecurity "restricted:latest": allowPrivilegeEscalation != false`
- **Fix:** Update the sidecar container's `securityContext`:
```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

#### B. Network Policy Blocking Egress
**Issue:** Network Policies blocked the backend pods from connecting to external services, including Cloud SQL and Google APIs.
- **Fix:** Update `network-policies.yaml` to allow Egress to:
    - **Cloud SQL:** Allow TCP ports `5432` (Postgres) and `3307` (Cloud SQL Proxy default).
    - **Google APIs:** Allow TCP port `443` (for Cloud SQL Admin API).
    - **GKE Metadata Server:** Allow TCP port `80` and `443` to `169.254.169.254` (required for Workload Identity).

#### C. DNS Resolution Failure
**Issue:** `cloud-sql-proxy` failed to resolve `sqladmin.googleapis.com` due to Network Policy blocking DNS.
- **Error:** `lookup sqladmin.googleapis.com: i/o timeout`
- **Fix:** Update `network-policies.yaml` to allow UDP/TCP port `53` to:
    - `kube-system` namespace (match label `kubernetes.io/metadata.name: kube-system`).
    - NodeLocal DNSCache IP `169.254.20.10/32`.

### 3. Load Balancer Health Checks
**Issue:** The Gateway (Google Cloud Load Balancer) could not reach the backend pods to perform health checks, marking them as unhealthy.
- **Fix:** Update `network-policies.yaml` to allow Ingress from Google Cloud health check IP ranges:
    - `35.191.0.0/16`
    - `130.211.0.0/22`

### 4. Frontend Network Policy Port Mismatch
**Issue:** Frontend pods were listening on port `80`, but the Network Policy only allowed Ingress on port `3000`.
- **Fix:** Update `network-policies.yaml` to allow Ingress on port `80` for the frontend service.

## Verification Steps

1.  **Check HTTPRoute Status:**
    ```bash
    kubectl get httproute -n backend -o yaml
    ```
    Ensure `conditions` show `Accepted: True` and `ResolvedRefs: True`.

2.  **Check Pod Logs:**
    ```bash
    kubectl logs -n backend -l app=backend -c cloud-sql-proxy
    ```
    Look for "The proxy has started successfully and is ready for new connections!".

3.  **Verify Site Access:**
    Navigate to the frontend URL and confirm the login page loads.
