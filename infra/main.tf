
# CoFound.ai Google Cloud Infrastructure
# Production-ready infrastructure with all required services

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
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

# Configure providers
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

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "firestore.googleapis.com"
  ])

  service = each.value
  disable_on_destroy = false
}

# VPC Network
resource "google_compute_network" "cofoundai_vpc" {
  name                    = "cofoundai-vpc-${var.environment}"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

# Subnet
resource "google_compute_subnetwork" "cofoundai_subnet" {
  name          = "cofoundai-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.cofoundai_vpc.id

  private_ip_google_access = true
}

# GKE Cluster
resource "google_container_cluster" "cofoundai_cluster" {
  name     = "cofoundai-cluster-${var.environment}"
  location = var.region
  
  remove_default_node_pool = true
  initial_node_count       = 1
  
  network    = google_compute_network.cofoundai_vpc.name
  subnetwork = google_compute_subnetwork.cofoundai_subnet.name

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  addons_config {
    horizontal_pod_autoscaling {
      disabled = false
    }
    http_load_balancing {
      disabled = false
    }
  }

  depends_on = [google_project_service.required_apis]
}

# GKE Node Pool
resource "google_container_node_pool" "cofoundai_nodes" {
  name       = "cofoundai-node-pool-${var.environment}"
  location   = var.region
  cluster    = google_container_cluster.cofoundai_cluster.name
  node_count = 2

  node_config {
    preemptible  = var.environment != "prod"
    machine_type = var.environment == "prod" ? "e2-standard-4" : "e2-medium"

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
    max_node_count = var.environment == "prod" ? 10 : 5
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

# Cloud SQL Instance
resource "google_sql_database_instance" "cofoundai_postgres" {
  name             = "cofoundai-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.environment == "prod" ? "db-custom-2-8192" : "db-f1-micro"
    
    disk_size = var.environment == "prod" ? 100 : 20
    disk_type = "PD_SSD"

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.cofoundai_vpc.id
      require_ssl     = true
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# Cloud SQL Database
resource "google_sql_database" "cofoundai_db" {
  name     = "cofoundai"
  instance = google_sql_database_instance.cofoundai_postgres.name
}

# Cloud SQL User
resource "google_sql_user" "cofoundai_user" {
  name     = "cofoundai"
  instance = google_sql_database_instance.cofoundai_postgres.name
  password = random_password.db_password.result
}

# Random password for database
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Private VPC Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.cofoundai_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.cofoundai_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Memorystore Redis Instance
resource "google_redis_instance" "cofoundai_redis" {
  name           = "cofoundai-redis-${var.environment}"
  memory_size_gb = var.environment == "prod" ? 5 : 1
  region         = var.region

  authorized_network = google_compute_network.cofoundai_vpc.id
  redis_version      = "REDIS_7_0"

  depends_on = [google_project_service.required_apis]
}

# Pub/Sub Topics
resource "google_pubsub_topic" "dream_requests" {
  name = "dream-requests-${var.environment}"
}

resource "google_pubsub_topic" "dream_responses" {
  name = "dream-responses-${var.environment}"
}

resource "google_pubsub_topic" "workflow_events" {
  name = "workflow-events-${var.environment}"
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "dream_processor" {
  name  = "dream-processor-${var.environment}"
  topic = google_pubsub_topic.dream_requests.name

  ack_deadline_seconds = 20
}

resource "google_pubsub_subscription" "workflow_monitor" {
  name  = "workflow-monitor-${var.environment}"
  topic = google_pubsub_topic.workflow_events.name

  ack_deadline_seconds = 60
}

# Cloud Storage Buckets
resource "google_storage_bucket" "cofoundai_artifacts" {
  name     = "cofoundai-artifacts-${var.project_id}-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "cofoundai_logs" {
  name     = "cofoundai-logs-${var.project_id}-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Artifact Registry for Container Images
resource "google_artifact_registry_repository" "cofoundai_images" {
  location      = var.region
  repository_id = "cofoundai-images-${var.environment}"
  description   = "CoFound.ai container images"
  format        = "DOCKER"
}

# Secret Manager for API Keys and Credentials
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key-${var.environment}"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "anthropic-api-key-${var.environment}"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-${var.environment}"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Store database URL in Secret Manager
resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${google_sql_user.cofoundai_user.name}:${random_password.db_password.result}@${google_sql_database_instance.cofoundai_postgres.private_ip_address}:5432/${google_sql_database.cofoundai_db.name}"
}

# IAM Roles for Service Accounts
resource "google_project_iam_member" "gke_sa_roles" {
  for_each = toset([
    "roles/storage.objectViewer",
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.client",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/aiplatform.user"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

# Cloud Build Trigger for CI/CD
resource "google_cloudbuild_trigger" "cofoundai_build" {
  name     = "cofoundai-build-${var.environment}"
  location = var.region

  github {
    owner = "your-github-username"  # Update this
    name  = "cofoundai"             # Update this
    push {
      branch = var.environment == "prod" ? "main" : "develop"
    }
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai_images.repository_id}/cofoundai:$COMMIT_SHA",
        "."
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai_images.repository_id}/cofoundai:$COMMIT_SHA"
      ]
    }

    step {
      name = "gcr.io/cloud-builders/gke-deploy"
      args = [
        "run",
        "--filename=k8s/",
        "--image=${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai_images.repository_id}/cofoundai:$COMMIT_SHA",
        "--location=${var.region}",
        "--cluster=${google_container_cluster.cofoundai_cluster.name}"
      ]
    }
  }
}

# Firestore Database
resource "google_firestore_database" "cofoundai_firestore" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.cofoundai_cluster.name
}

output "cluster_endpoint" {
  value = google_container_cluster.cofoundai_cluster.endpoint
}

output "database_connection_name" {
  value = google_sql_database_instance.cofoundai_postgres.connection_name
}

output "redis_host" {
  value = google_redis_instance.cofoundai_redis.host
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.cofoundai_images.repository_id}"
}

output "storage_bucket_artifacts" {
  value = google_storage_bucket.cofoundai_artifacts.name
}
