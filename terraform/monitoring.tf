# Google Cloud Monitoring & Alerting Configuration

# Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "DevOps Team Email"
  type         = "email"
  project      = var.project_id
  labels = {
    email_address = "devops@example.com" # Replace with actual email
  }
}

# ------------------------------------------------------------------------------
# Alert Policies
# ------------------------------------------------------------------------------

# 1. High CPU Utilization Alert
resource "google_monitoring_alert_policy" "high_cpu" {
  display_name = "GKE Container High CPU Usage"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "CPU usage > 80%"
    condition_threshold {
      filter     = "resource.type = \"k8s_container\" AND metric.type = \"kubernetes.io/container/cpu/limit_utilization\""
      duration   = "300s" # 5 minutes
      comparison = "COMPARISON_GT"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
      threshold_value = 0.8 # 80%
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  documentation {
    content = "Container CPU usage is above 80% for 5 minutes. Check if scaling is working or if limits need adjustment."
  }
}

# 2. High Memory Utilization Alert
resource "google_monitoring_alert_policy" "high_memory" {
  display_name = "GKE Container High Memory Usage"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "Memory usage > 85%"
    condition_threshold {
      filter     = "resource.type = \"k8s_container\" AND metric.type = \"kubernetes.io/container/memory/limit_utilization\""
      duration   = "300s"
      comparison = "COMPARISON_GT"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
      threshold_value = 0.85 # 85%
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  documentation {
    content = "Container Memory usage is above 85% for 5 minutes. Risk of OOMKill. Check for memory leaks or increase limits."
  }
}

# 3. Container Restart Alert (CrashLoopBackOff detection)
resource "google_monitoring_alert_policy" "container_restarts" {
  display_name = "GKE Container High Restart Rate"
  combiner     = "OR"
  project      = var.project_id

  conditions {
    display_name = "Restarts > 3 in 15 mins"
    condition_threshold {
      filter     = "resource.type = \"k8s_container\" AND metric.type = \"kubernetes.io/container/restart_count\""
      duration   = "900s" # 15 minutes
      comparison = "COMPARISON_GT"
      aggregations {
        alignment_period   = "900s"
        per_series_aligner = "ALIGN_DELTA"
      }
      threshold_value = 3
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  documentation {
    content = "Container is restarting frequently. Check logs for crash reasons (CrashLoopBackOff)."
  }
}

# ------------------------------------------------------------------------------
# Monitoring Dashboard
# ------------------------------------------------------------------------------

resource "google_monitoring_dashboard" "gke_dashboard" {
  project        = var.project_id
  dashboard_json = file("${path.module}/dashboards/gke-overview.json")
}
