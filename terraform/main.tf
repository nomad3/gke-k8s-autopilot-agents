# Main Terraform Configuration for GKE Autopilot Migration

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_id          = var.project_id
  region              = var.region
  network_name        = var.network_name
  subnet_name         = var.subnet_name
  subnet_cidr         = var.subnet_cidr
  pods_cidr_name      = var.pods_cidr_name
  pods_cidr_range     = var.pods_cidr_range
  services_cidr_name  = var.services_cidr_name
  services_cidr_range = var.services_cidr_range
  cluster_name        = var.cluster_name
}

# GKE Module
module "gke" {
  source = "./modules/gke"

  project_id                      = var.project_id
  region                          = var.region
  cluster_name                    = var.cluster_name
  network_id                      = module.vpc.network_id
  subnet_id                       = module.vpc.subnet_id
  pods_range_name                 = module.vpc.pods_range_name
  services_range_name             = module.vpc.services_range_name
  master_ipv4_cidr_block          = var.master_ipv4_cidr_block
  authorized_networks             = var.authorized_networks
  enable_binary_authorization     = var.enable_binary_authorization
  release_channel                 = var.release_channel
  enable_vertical_pod_autoscaling = var.enable_vertical_pod_autoscaling
  labels                          = var.labels
  environment                     = var.environment
}

# DB Module
module "db" {
  source = "./modules/db"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  network_id    = module.vpc.network_id
  db_tier       = var.environment == "prod" ? "db-custom-2-7680" : "db-g1-small"
  db_version    = "POSTGRES_15"
  db_storage_gb = var.environment == "prod" ? 100 : 10
  enable_ha     = var.environment == "prod" ? true : false
  labels        = var.labels
}

# DNS Module (optional)
module "dns" {
  count  = var.enable_dns ? 1 : 0
  source = "./modules/dns"

  project_id  = var.project_id
  domain_name = var.domain_name
  environment = var.environment
  dns_records = var.dns_records
  gateway_ip  = var.gateway_ip
  labels      = var.labels
}


# ========================================
# Moved Blocks
# ========================================

# VPC
moved {
  from = google_compute_network.vpc
  to   = module.vpc.google_compute_network.vpc
}

moved {
  from = google_compute_subnetwork.subnet
  to   = module.vpc.google_compute_subnetwork.subnet
}

moved {
  from = google_compute_router.router
  to   = module.vpc.google_compute_router.router
}

moved {
  from = google_compute_router_nat.nat
  to   = module.vpc.google_compute_router_nat.nat
}

moved {
  from = google_compute_firewall.allow_health_checks
  to   = module.vpc.google_compute_firewall.allow_health_checks
}

# GKE
moved {
  from = google_container_cluster.autopilot
  to   = module.gke.google_container_cluster.autopilot
}

moved {
  from = google_service_account.gke_sa
  to   = module.gke.google_service_account.gke_sa
}

moved {
  from = google_project_iam_member.gke_sa_log_writer
  to   = module.gke.google_project_iam_member.gke_sa_log_writer
}

moved {
  from = google_project_iam_member.gke_sa_metric_writer
  to   = module.gke.google_project_iam_member.gke_sa_metric_writer
}

moved {
  from = google_project_iam_member.gke_sa_monitoring_viewer
  to   = module.gke.google_project_iam_member.gke_sa_monitoring_viewer
}

moved {
  from = google_project_iam_member.gke_sa_artifact_registry
  to   = module.gke.google_project_iam_member.gke_sa_artifact_registry
}

# DB
moved {
  from = google_secret_manager_secret.database_password
  to   = module.db.google_secret_manager_secret.database_password
}

moved {
  from = google_secret_manager_secret.database_url
  to   = module.db.google_secret_manager_secret.database_url
}
