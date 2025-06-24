# CoFound.ai Google Cloud Infrastructure
# Production-ready infrastructure with all required services

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
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

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# Configure providers
provider "google" {
  credentials = file("../terraform-sa-key.json")
  project     = var.project_id
  region      = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "redis.googleapis.com"
  ])

  service = each.value
  disable_dependent_services = false
}

# VPC Network
resource "google_compute_network" "cofoundai_vpc" {
  name                    = "cofoundai-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

# Subnet
resource "google_compute_subnetwork" "cofoundai_subnet" {
  name          = "cofoundai-subnet"
  ip_cidr_range = "10.1.0.0/16"
  region        = var.region
  network       = google_compute_network.cofoundai_vpc.name

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.2.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.3.0.0/16"
  }
}

# GKE Cluster
resource "google_container_cluster" "cofoundai_cluster" {
  name     = "cofoundai-cluster"
  location = var.region

  # Network configuration
  network    = google_compute_network.cofoundai_vpc.name
  subnetwork = google_compute_subnetwork.cofoundai_subnet.name

  # IP allocation policy
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network policy
  network_policy {
    enabled = true
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Security
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Resource labels
  resource_labels = {
    environment = var.environment
    project     = "cofoundai"
  }

  depends_on = [google_project_service.apis]
}

# GKE Node Pool
resource "google_container_node_pool" "cofoundai_nodes" {
  name       = "cofoundai-node-pool"
  location   = var.region
  cluster    = google_container_cluster.cofoundai_cluster.name
  node_count = 2

  # Auto-scaling
  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  # Node configuration
  node_config {
    preemptible  = false
    machine_type = "e2-standard-2"
    disk_size_gb = 50
    disk_type    = "pd-standard"

    # Service account  
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      app         = "cofoundai"
    }

    tags = ["cofoundai-node"]
  }

  # Management
  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Service Account for GKE Nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "cofoundai-gke-nodes"
  display_name = "CoFound.ai GKE Nodes"
}

# IAM will be handled manually via gcloud commands
# resource "google_project_iam_member" "gke_nodes_editor" {
#   project = var.project_id
#   role    = "roles/editor"
#   member  = "serviceAccount:${google_service_account.gke_nodes.email}"
# }

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "cofoundai_db" {
  name             = "cofoundai-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-custom-1-3840"
    availability_type = "ZONAL"
    disk_size         = 20
    disk_type         = "PD_SSD"

    database_flags {
      name  = "max_connections"
      value = "200"
    }

    backup_configuration {
      enabled                        = true
      start_time                    = "02:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled                                  = true
      # Temporarily disable private network due to permission issues
      # private_network                               = google_compute_network.cofoundai_vpc.id
      # enable_private_path_for_google_cloud_services = true
    }

    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }
  }

  deletion_protection = true

  # Private VPC Connection for Cloud SQL - temporarily disabled due to permissions
  # depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Private VPC Connection for Cloud SQL - temporarily disabled due to permissions
# resource "google_service_networking_connection" "private_vpc_connection" {
#   network                 = google_compute_network.cofoundai_vpc.id
#   service                 = "servicenetworking.googleapis.com"
#   reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
# }

# Private VPC Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.cofoundai_vpc.id
}

# Database and User
resource "google_sql_database" "cofoundai_database" {
  name     = "cofoundai"
  instance = google_sql_database_instance.cofoundai_db.name
}

resource "google_sql_user" "cofoundai_user" {
  name     = "cofoundai_user"
  instance = google_sql_database_instance.cofoundai_db.name
  password = "CoFoundAI2025!"
}

# Store DB password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "database-password"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = "CoFoundAI2025!"
}

# Memorystore Redis
resource "google_redis_instance" "cofoundai_cache" {
  name               = "cofoundai-redis-${var.environment}"
  memory_size_gb     = 2
  region             = var.region
  location_id        = "${var.region}-a"
  redis_version      = "REDIS_7_0"
  display_name       = "CoFound.ai Redis Cache"
  
  authorized_network = google_compute_network.cofoundai_vpc.id
  
  auth_enabled = true
  
  labels = {
    environment = var.environment
    project     = "cofoundai"
  }
}

# Cloud Storage Bucket
resource "google_storage_bucket" "cofoundai_storage" {
  name     = "${var.project_id}-cofoundai-storage-${var.environment}"
  location = "US"

  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 7
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = "cofoundai"
  }
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "cofoundai_repo" {
  location      = var.region
  repository_id = "cofoundai-repo"
  description   = "CoFound.ai Docker repository"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    project     = "cofoundai"
  }
}

# Pub/Sub Topics
resource "google_pubsub_topic" "dream_requests" {
  name = "dream-requests-${var.environment}"

  labels = {
    environment = var.environment
    phase       = "dream"
  }
}

resource "google_pubsub_topic" "dream_processed" {
  name = "dream-processed-${var.environment}"

  labels = {
    environment = var.environment
    phase       = "dream"
  }
}

resource "google_pubsub_topic" "maturation_requests" {
  name = "maturation-requests-${var.environment}"

  labels = {
    environment = var.environment
    phase       = "maturation"
  }
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "dream_subscription" {
  name  = "dream-subscription-${var.environment}"
  topic = google_pubsub_topic.dream_requests.name

  ack_deadline_seconds = 300
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "dead_letter" {
  name = "dead-letter-${var.environment}"
}

# Firewall Rules
resource "google_compute_firewall" "allow_gke_ingress" {
  name    = "allow-gke-ingress"
  network = google_compute_network.cofoundai_vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["cofoundai-node"]
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.cofoundai_cluster.name
}

output "cluster_location" {
  value = google_container_cluster.cofoundai_cluster.location
}

output "cluster_endpoint" {
  value = google_container_cluster.cofoundai_cluster.endpoint
  sensitive = true
}

output "database_connection_name" {
  value = google_sql_database_instance.cofoundai_db.connection_name
}

output "database_private_ip" {
  value = google_sql_database_instance.cofoundai_db.private_ip_address
}

output "redis_host" {
  value = google_redis_instance.cofoundai_cache.host
}

output "redis_port" {
  value = google_redis_instance.cofoundai_cache.port
}

output "storage_bucket_name" {
  value = google_storage_bucket.cofoundai_storage.name
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai_repo.repository_id}"
}
