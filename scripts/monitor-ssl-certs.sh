#!/bin/bash

# SSL Certificate Monitoring Script
# Monitors Google Cloud Certificate Manager certificate provisioning status

PROJECT_ID="ai-agency-479516"
CERT_NAME="agentprovision-cert"
GATEWAY_NAME="external-gateway"
GATEWAY_NAMESPACE="gateway-system"

echo "🔍 Monitoring SSL Certificate Provisioning Status"
echo "=================================================="
echo ""

# Function to get certificate status
check_cert_status() {
    echo "📜 Certificate Status:"
    gcloud certificate-manager certificates describe "$CERT_NAME" \
        --project="$PROJECT_ID" \
        --format="table(managed.state,managed.authorizationAttemptInfo.domain,managed.authorizationAttemptInfo.state)"
    echo ""
}

# Function to check Gateway status
check_gateway_status() {
    echo "🌐 Gateway Status:"
    kubectl get gateway "$GATEWAY_NAME" -n "$GATEWAY_NAMESPACE" \
        -o jsonpath='{.status.conditions[?(@.type=="Programmed")]}' | jq -r '.status + " - " + .reason'
    echo ""
}

# Function to test HTTPS endpoints
test_endpoints() {
    echo "🧪 Testing HTTPS Endpoints:"
    
    domains=("scdp-api-prod.agentprovision.com" "scdp-front-prod.agentprovision.com" "scdp-mcp-prod.agentprovision.com")
    
    for domain in "${domains[@]}"; do
        echo -n "  $domain: "
        if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "https://$domain" 2>/dev/null | grep -q "200\|301\|302\|404"; then
            echo "✅ Responding"
        else
            echo "❌ Not responding (expected during provisioning)"
        fi
    done
    echo ""
}

# Main monitoring loop
while true; do
    clear
    echo "🔍 Monitoring SSL Certificate Provisioning Status"
    echo "=================================================="
    echo "Time: $(date)"
    echo ""
    
    check_cert_status
    check_gateway_status
    test_endpoints
    
    # Check if all certificates are active
    CERT_STATE=$(gcloud certificate-manager certificates describe "$CERT_NAME" \
        --project="$PROJECT_ID" \
        --format="value(managed.state)")
    
    if [ "$CERT_STATE" = "ACTIVE" ]; then
        echo "🎉 SUCCESS! All certificates are ACTIVE!"
        echo ""
        echo "You can now access your services via HTTPS:"
        echo "  - https://scdp-api-prod.agentprovision.com"
        echo "  - https://scdp-front-prod.agentprovision.com"
        echo "  - https://scdp-mcp-prod.agentprovision.com"
        break
    fi
    
    echo "⏳ Waiting 30 seconds before next check..."
    echo "   (Press Ctrl+C to stop monitoring)"
    sleep 30
done
