
# CoFound.ai Google Cloud Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Provider Configuration
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "container.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "aiplatform.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "cofoundai-vpc-${var.environment}"
  auto_create_subnetworks = false
  depends_on             = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "cofoundai-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.2.0.0/16"
  }
}

# Cloud NAT for private instances
resource "google_compute_router" "router" {
  name    = "cofoundai-router-${var.environment}"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "cofoundai-router-nat-${var.environment}"
  router                            = google_compute_router.router.name
  region                            = var.region
  nat_ip_allocate_option            = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "cofoundai-gke-${var.environment}"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.subnet.id

  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  depends_on = [google_project_service.apis]
}

resource "google_container_node_pool" "primary_preemptible_nodes" {
  name       = "main-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 2

  node_config {
    preemptible  = true
    machine_type = "e2-medium"

    service_account = google_service_account.gke_service_account.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Service Account for GKE
resource "google_service_account" "gke_service_account" {
  account_id   = "cofoundai-gke-sa-${var.environment}"
  display_name = "CoFound.ai GKE Service Account"
}

resource "google_project_iam_member" "gke_service_account_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/stackdriver.resourceMetadata.writer"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Cloud SQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = "cofoundai-postgres-${var.environment}"
  database_version = "POSTGRES_14"
  region          = var.region
  deletion_protection = false

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.vpc.id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private VPC Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Cloud SQL Database
resource "google_sql_database" "cofoundai_db" {
  name     = "cofoundai"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "db_user" {
  name     = "cofoundai"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Memorystore Redis
resource "google_redis_instance" "cache" {
  name           = "cofoundai-redis-${var.environment}"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  depends_on = [google_project_service.apis]
}

# Pub/Sub Topics
resource "google_pubsub_topic" "dream_requested" {
  name = "dream-requested-${var.environment}"
}

resource "google_pubsub_topic" "dream_processed" {
  name = "dream-processed-${var.environment}"
}

resource "google_pubsub_topic" "blueprint_generated" {
  name = "blueprint-generated-${var.environment}"
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "dream_requested_sub" {
  name  = "dream-requested-sub-${var.environment}"
  topic = google_pubsub_topic.dream_requested.name

  ack_deadline_seconds = 20

  retry_policy {
    minimum_retry_delay = "1s"
    maximum_retry_delay = "60s"
  }
}

resource "google_pubsub_subscription" "dream_processed_sub" {
  name  = "dream-processed-sub-${var.environment}"
  topic = google_pubsub_topic.dream_processed.name

  ack_deadline_seconds = 20
}

# Secret Manager
resource "google_secret_manager_secret" "db_connection" {
  secret_id = "db-connection-${var.environment}"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "db_connection" {
  secret = google_secret_manager_secret.db_connection.id
  secret_data = jsonencode({
    host     = google_sql_database_instance.postgres.private_ip_address
    database = google_sql_database.cofoundai_db.name
    username = google_sql_user.db_user.name
    password = google_sql_user.db_user.password
  })
}

resource "google_secret_manager_secret" "redis_connection" {
  secret_id = "redis-connection-${var.environment}"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "redis_connection" {
  secret = google_secret_manager_secret.redis_connection.id
  secret_data = jsonencode({
    host = google_redis_instance.cache.host
    port = google_redis_instance.cache.port
  })
}

# Artifact Registry
resource "google_artifact_registry_repository" "cofoundai" {
  location      = var.region
  repository_id = "cofoundai-${var.environment}"
  description   = "CoFound.ai Docker images"
  format        = "DOCKER"
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_location" {
  value = google_container_cluster.primary.location
}

output "database_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai.repository_id}"
}
