# CoFound.ai Google Cloud Platform Deployment Rehberi

## 1. Google Cloud Platform Hesabı Açma ve Kurulum

### 1.1 GCP Hesabı Oluşturma
1. **Google Cloud Console**'a gidin: https://console.cloud.google.com/
2. **Google hesabınızla giriş yapın** (yoksa oluşturun)
3. **Ücretsiz deneme** için $300 kredi alın (kredi kartı gerekli ama ücret yok)
4. **Faturalandırma hesabı** oluşturun

### 1.2 Yeni Proje Oluşturma
```bash
# Proje adı: cofoundai-production
# Proje ID: cofoundai-prod-[RANDOM_ID]
```

### 1.3 Gerekli API'ları Etkinleştirme
Aşağıdaki API'ları etkinleştirin:
- **Compute Engine API** (VM'ler için)
- **Google Kubernetes Engine API** (Container orchestration)
- **Cloud SQL API** (Veritabanı)
- **Cloud Storage API** (Dosya depolama)
- **Pub/Sub API** (Mesajlaşma)
- **Secret Manager API** (Güvenli key saklama)
- **Vertex AI API** (LLM'ler için)
- **Cloud Build API** (CI/CD için)
- **Artifact Registry API** (Container images)

### 1.4 Local Development Ortamı Kurma

#### Google Cloud SDK Kurulumu (Windows)
1. **Google Cloud SDK**'yı indirin: https://cloud.google.com/sdk/docs/install
2. **PowerShell**'i yönetici olarak açın
3. SDK'yı kurun ve authenticate olun:

```powershell
# Google Cloud SDK kurulumu
gcloud init

# Authenticate
gcloud auth login

# Proje seçin
gcloud config set project [YOUR_PROJECT_ID]

# Application Default Credentials
gcloud auth application-default login
```

#### Docker Desktop Kurulumu
1. **Docker Desktop**'ı indirin: https://www.docker.com/products/docker-desktop
2. Windows için kurun ve restart yapın
3. Docker'ın çalıştığını kontrol edin:

```powershell
docker --version
docker run hello-world
```

#### Kubectl Kurulumu
```powershell
# Kubernetes command-line tool
gcloud components install kubectl

# Kontrol
kubectl version --client
```

## 2. Infrastructure Kurulumu (Terraform ile)

### 2.1 Terraform Kurulumu
1. **Terraform**'u indirin: https://www.terraform.io/downloads
2. PATH'e ekleyin
3. Kontrol edin:

```powershell
terraform --version
```

### 2.2 GCP Service Account Oluşturma
```bash
# Service account oluştur
gcloud iam service-accounts create cofoundai-terraform \
    --description="Terraform service account for CoFound.ai" \
    --display-name="CoFound.ai Terraform"

# Roller ataması
gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
    --member="serviceAccount:cofoundai-terraform@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/editor"

# Key dosyası oluştur
gcloud iam service-accounts keys create ./terraform-sa-key.json \
    --iam-account=cofoundai-terraform@[YOUR_PROJECT_ID].iam.gserviceaccount.com
```

### 2.3 Terraform Konfigürasyonu

#### terraform/main.tf dosyasını güncelleme:
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file("../terraform-sa-key.json")
  project     = var.project_id
  region      = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# GKE Cluster
resource "google_container_cluster" "cofoundai_cluster" {
  name     = "cofoundai-cluster"
  location = var.region

  # Node configuration
  initial_node_count       = 1
  remove_default_node_pool = true

  # Network configuration
  network    = "default"
  subnetwork = "default"

  # Security
  enable_binary_authorization = false
  enable_network_policy       = true
}

# Node Pool
resource "google_container_node_pool" "cofoundai_nodes" {
  name       = "cofoundai-node-pool"
  location   = var.region
  cluster    = google_container_cluster.cofoundai_cluster.name
  node_count = 2

  node_config {
    preemptible  = false
    machine_type = "e2-medium"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      environment = "production"
      app         = "cofoundai"
    }
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "cofoundai_db" {
  name             = "cofoundai-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "cofoundai_database" {
  name     = "cofoundai"
  instance = google_sql_database_instance.cofoundai_db.name
}

resource "google_sql_user" "cofoundai_user" {
  name     = "cofoundai_user"
  instance = google_sql_database_instance.cofoundai_db.name
  password = "SecurePassword123!"
}

# Memorystore Redis
resource "google_redis_instance" "cofoundai_cache" {
  name         = "cofoundai-redis"
  memory_size_gb = 1
  region       = var.region
  
  redis_version = "REDIS_7_0"
}

# Cloud Storage Bucket
resource "google_storage_bucket" "cofoundai_storage" {
  name     = "${var.project_id}-cofoundai-storage"
  location = "US"

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

# Pub/Sub Topics
resource "google_pubsub_topic" "dream_requests" {
  name = "dream-requests"
}

resource "google_pubsub_topic" "dream_processed" {
  name = "dream-processed"
}

resource "google_pubsub_subscription" "dream_subscription" {
  name  = "dream-subscription"
  topic = google_pubsub_topic.dream_requests.name

  ack_deadline_seconds = 20
}

# Outputs
output "cluster_name" {
  value = google_container_cluster.cofoundai_cluster.name
}

output "cluster_location" {
  value = google_container_cluster.cofoundai_cluster.location
}

output "database_ip" {
  value = google_sql_database_instance.cofoundai_db.public_ip_address
}

output "redis_host" {
  value = google_redis_instance.cofoundai_cache.host
}
```

## 3. Development ve Deployment İş Akışı

### 3.1 Local Development Ortamı
1. **CoFound.ai projesini clone** edin (zaten var)
2. **Virtual environment** oluşturun:

```powershell
cd C:\Users\bilal\OneDrive\Masaüstü\cofoundai

# Python virtual environment
python -m venv venv
.\venv\Scripts\activate

# Dependencies yükle
pip install -r requirements.txt
```

3. **Environment variables** ayarlayın:

```powershell
# .env dosyası oluştur (config.env.example'ı kopyala)
copy config.env.example .env

# .env dosyasını düzenle:
# - GOOGLE_CLOUD_PROJECT=your-project-id
# - DEVELOPMENT_MODE=false
# - LLM_PROVIDER=openai veya google
```

### 3.2 Docker Containerization

#### Dockerfile oluşturma (services/dream-service/):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Environment
ENV PYTHONPATH=/app
ENV DEVELOPMENT_MODE=false

# Port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start command
CMD ["python", "main.py"]
```

### 3.3 Kubernetes Manifests

#### k8s/dream-service-deployment.yaml:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dream-service
  labels:
    app: dream-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dream-service
  template:
    metadata:
      labels:
        app: dream-service
    spec:
      containers:
      - name: dream-service
        image: gcr.io/PROJECT_ID/dream-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT
          value: "PROJECT_ID"
        - name: DATABASE_HOST
          value: "DB_IP"
        - name: REDIS_HOST
          value: "REDIS_IP"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: dream-service
spec:
  selector:
    app: dream-service
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

## 4. CI/CD Pipeline (Cloud Build)

### 4.1 cloudbuild.yaml:
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'gcr.io/$PROJECT_ID/dream-service:$COMMIT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/dream-service:latest',
      './services/dream-service'
    ]

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/dream-service:$COMMIT_SHA']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/dream-service:latest']

  # Deploy to GKE
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
    - run
    - --filename=k8s/dream-service-deployment.yaml
    - --image=gcr.io/$PROJECT_ID/dream-service:$COMMIT_SHA
    - --location=us-central1
    - --cluster=cofoundai-cluster

options:
  logging: CLOUD_LOGGING_ONLY
```

## 5. Deployment Adımları

### 5.1 Infrastructure Deploy
```powershell
# Terraform klasörüne git
cd infra

# Variables dosyası oluştur
echo 'project_id = "your-project-id"' > terraform.tfvars

# Initialize
terraform init

# Plan
terraform plan

# Apply (infrastructure oluştur)
terraform apply
```

### 5.2 Application Deploy
```powershell
# Cluster credentials al
gcloud container clusters get-credentials cofoundai-cluster --region=us-central1

# Docker image build ve push
cd services/dream-service
docker build -t gcr.io/[PROJECT_ID]/dream-service .
docker push gcr.io/[PROJECT_ID]/dream-service

# Kubernetes deploy
kubectl apply -f ../../k8s/dream-service-deployment.yaml

# Service status kontrol
kubectl get services
kubectl get pods
```

## 6. Monitoring ve Logging

### 6.1 Cloud Logging
```bash
# Logs görüntüle
gcloud logging read "resource.type=k8s_container AND resource.labels.container_name=dream-service"
```

### 6.2 Cloud Monitoring
- **GCP Console** > **Monitoring** > **Dashboards**
- **Kubernetes Engine** > **Workloads** bölümünden pod durumları

## 7. Production Test

### 7.1 API Test
```bash
# Load balancer IP al
kubectl get services dream-service

# Test request
curl -X POST http://[LOAD_BALANCER_IP]/dream/process \
  -H "Content-Type: application/json" \
  -d '{"project_description": "Test todo app", "user_id": "test"}'
```

### 7.2 LLM Integration Test
```python
import requests

# Dream API test
response = requests.post(
    "http://[LOAD_BALANCER_IP]/dream/process",
    json={
        "project_description": "Modern bir e-ticaret sitesi",
        "user_id": "test_user"
    }
)

print(response.json())
```

## Başarı! 🎉

Bu adımları takip ettikten sonra CoFound.ai sisteminiz Google Cloud Platform'da production'da çalışacak.

### Sonraki Adımlar:
1. **Domain name** ayarlayın
2. **SSL certificate** ekleyin
3. **Monitoring** ve **alerting** kurun
4. **Backup** stratejisi oluşturun
5. **Scaling** politikaları belirleyin 