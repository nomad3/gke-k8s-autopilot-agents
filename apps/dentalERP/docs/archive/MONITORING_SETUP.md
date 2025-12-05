# 📊 Monitoring & Observability Setup

## Overview

Comprehensive monitoring stack for DentalERP platform using Prometheus and Grafana.

---

## 🚀 Quick Start

### Start Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
open http://localhost:3003  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

---

## 📊 **What Gets Monitored**

### **1. MCP Server Metrics**
- Request rate and latency
- Integration connector health
- Cache hit/miss rates
- Sync job success/failure rates
- External API response times

### **2. ERP Backend Metrics**
- API endpoint response times
- Authentication success/failure
- WebSocket connections
- Database query performance

### **3. PostgreSQL Metrics**
- Connection pool usage
- Query performance
- Database size
- Transaction rate

### **4. Redis Metrics**
- Memory usage
- Cache hit rate
- Eviction rate
- Connection count

### **5. System Metrics**
- CPU usage
- Memory usage
- Disk I/O
- Network throughput

### **6. Snowflake Cost Tracking**
- Credits used per warehouse
- Query execution times
- Data scanned (GB)
- Estimated daily cost

---

## 🎯 **Key Dashboards**

### **Platform Overview Dashboard**
- All services health status
- Request rates across services
- Error rates
- Response time p95/p99

### **MCP Integration Dashboard**
- NetSuite connector status
- ADP connector status
- Sync job success rates
- Data pipeline latency

### **Cost Monitoring Dashboard**
- Snowflake daily spend
- Credits used by warehouse
- Most expensive queries
- Cost optimization recommendations

### **Database Performance**
- PostgreSQL connection pool
- Slow query log
- Cache hit ratios
- Table sizes

---

## 🔔 **Alerting Rules** (To Configure)

### **Critical Alerts**
- Service down (any component)
- MCP sync failures > 50%
- Database connection pool exhausted
- Snowflake daily cost > $500

### **Warning Alerts**
- API response time > 2s (p95)
- Redis memory > 80%
- Disk usage > 85%
- Integration connector errors > 10%

---

## 📈 **Snowflake Cost Monitoring**

### **Query Cost Monitoring Table**
```sql
-- dbt model: gold.operations.snowflake_cost_monitoring
SELECT * FROM gold.snowflake_cost_monitoring
WHERE usage_date >= CURRENT_DATE() - 7
ORDER BY estimated_cost_usd DESC
```

### **Daily Cost Alerts**
Run daily via cron:
```bash
# Check if daily cost exceeds threshold
DAILY_COST=$(snowsql -q "SELECT SUM(estimated_cost_usd) FROM gold.snowflake_cost_monitoring WHERE usage_date = CURRENT_DATE()")

if [ $DAILY_COST -gt 500 ]; then
  # Send alert
  echo "Snowflake cost alert: \$${DAILY_COST}" | mail -s "Cost Alert" admin@dentalerp.com
fi
```

---

## 🛠️ **Setup Instructions**

### **1. Start Monitoring Stack**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### **2. Access Grafana**
- URL: http://localhost:3003
- Default credentials: admin / admin
- Change password on first login

### **3. Import Dashboards**
Grafana dashboards are in `/monitoring/grafana/dashboards/`
- Import via UI: Configuration → Dashboards → Import

### **4. Configure Alerts**
- Add Alertmanager configuration
- Set up email/Slack channels
- Configure alert rules in Prometheus

---

## 📊 **Metrics to Track**

### **Business Metrics (from Snowflake)**
- Daily revenue
- New patient acquisition
- Appointment completion rate
- Collection rate

### **Technical Metrics (from Prometheus)**
- API latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connections
- Cache hit rate

### **Cost Metrics (from Snowflake)**
- Credits used per day
- Cost per query
- Most expensive tables
- Warehouse utilization

---

## 🎯 **Performance Targets**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time (p95) | < 200ms | > 2s |
| MCP Sync Success Rate | > 99% | < 95% |
| Cache Hit Rate | > 90% | < 70% |
| Database Connection Pool | < 80% | > 90% |
| Snowflake Daily Cost | < $300 | > $500 |

---

## 📚 **Resources**

- **Prometheus**: https://prometheus.io/docs
- **Grafana**: https://grafana.com/docs
- **Snowflake Cost**: https://docs.snowflake.com/en/user-guide/cost-understanding

---

**Last Updated**: October 26, 2025
**Status**: Ready to Deploy
