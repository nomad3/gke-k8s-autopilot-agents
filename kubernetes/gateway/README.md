# Gateway API Configuration

This directory contains configuration for the Kubernetes Gateway API on GKE. We use the GKE-native `gke-l7-global-external-managed` GatewayClass to provision a global external Application Load Balancer.

## Overview

The Gateway API replaces the traditional Ingress API for managing external access to services.

- **Gateway**: Defines the load balancer (one per cluster/environment).
- **HTTPRoute**: Defines routing rules (one per service).

## Files

- `gateway.yaml`: The shared Gateway resource.
- `namespace.yaml`: The `gateway-system` namespace.

## Deployment

1. **Create Namespace**:
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. **Deploy Gateway**:
   ```bash
   kubectl apply -f gateway.yaml
   ```

3. **Verify**:
   ```bash
   kubectl get gateway -n gateway-system
   ```
   Wait for the `PROGRAMMED` status to be `True`.

4. **Get IP Address**:
   ```bash
   kubectl get gateway external-gateway -n gateway-system -o jsonpath='{.status.addresses[0].value}'
   ```
   Update your DNS records to point to this IP.

## HTTPRoutes

HTTPRoutes are deployed via Helm charts with the application. See `helm/charts/microservice/values.yaml` for configuration.

Example `HTTPRoute` configuration in values:

```yaml
gateway:
  enabled: true
  gatewayName: external-gateway
  gatewayNamespace: gateway-system
  hostnames:
    - app.example.com
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: my-service
          port: 80
```
