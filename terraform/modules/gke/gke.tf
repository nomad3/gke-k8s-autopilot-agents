# GKE Autopilot Cluster
resource "google_container_cluster" "autopilot" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # Enable Autopilot mode
  enable_autopilot = true

  # Network configuration
  network    = var.network_id
  subnetwork = var.subnet_id

  # IP allocation policy for VPC-native cluster
  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private cluster configuration
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # Set to true for fully private cluster
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  # Master authorized networks (restrict API access)
  dynamic "master_authorized_networks_config" {
    for_each = length(var.authorized_networks) > 0 ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Workload Identity for pod authentication
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Binary Authorization for image security
  binary_authorization {
    evaluation_mode = var.enable_binary_authorization ? "PROJECT_SINGLETON_POLICY_ENFORCE" : "DISABLED"
  }

  # Release channel for automatic updates
  release_channel {
    channel = var.release_channel
  }

  # Vertical Pod Autoscaling
  vertical_pod_autoscaling {
    enabled = var.enable_vertical_pod_autoscaling
  }

  # Maintenance window (reduces disruption)
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00" # 3 AM in cluster's timezone
    }
  }

  # Monitoring and logging configuration
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
    managed_prometheus {
      enabled = true
    }
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  # Enable Dataplane V2 (required for Autopilot)
  datapath_provider = "ADVANCED_DATAPATH"

  # Resource labels
  resource_labels = merge(
    var.labels,
    {
      environment = var.environment
      cluster     = var.cluster_name
    }
  )

  # Deletion protection (enabled for prod, disabled for dev)
  deletion_protection = var.environment == "prod" ? true : false
}
