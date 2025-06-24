#!/bin/bash

# CoFound.ai Google Cloud Platform Setup Script
# Bu script CoFound.ai sistemini GCP'de kurmak için gerekli adımları otomatikleştirir

set -e  # Exit on any error

# Renkli output için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if required tools are installed
check_prerequisites() {
    log "Ön koşullar kontrol ediliyor..."
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        error "Google Cloud SDK kurulu değil. Lütfen önce kurun: https://cloud.google.com/sdk/docs/install"
    fi
    
    # Check terraform
    if ! command -v terraform &> /dev/null; then
        error "Terraform kurulu değil. Lütfen önce kurun: https://www.terraform.io/downloads"
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        warn "kubectl kurulu değil. Google Cloud SDK ile kuruluyor..."
        gcloud components install kubectl
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        error "Docker kurulu değil. Lütfen önce kurun: https://www.docker.com/get-started"
    fi
    
    log "Tüm ön koşullar hazır ✅"
}

# Get user input
get_user_input() {
    log "Proje bilgilerini girmeniz gerekiyor..."
    
    # Project ID
    while [[ -z "$PROJECT_ID" ]]; do
        read -p "Google Cloud Project ID girin: " PROJECT_ID
        if [[ -z "$PROJECT_ID" ]]; then
            warn "Project ID boş olamaz!"
        fi
    done
    
    # Region
    read -p "Hangi region kullanmak istiyorsunuz? (default: us-central1): " REGION
    REGION=${REGION:-us-central1}
    
    # Domain (optional)
    read -p "Domain adınız var mı? (örn: cofoundai.com, yoksa Enter basın): " DOMAIN
    
    # OpenAI API Key
    read -s -p "OpenAI API Key girin (LLM için): " OPENAI_API_KEY
    echo
    
    if [[ -z "$OPENAI_API_KEY" ]]; then
        error "OpenAI API Key gerekli!"
    fi
    
    # Confirm
    echo
    echo -e "${BLUE}Girilen bilgiler:${NC}"
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Domain: ${DOMAIN:-'Yok'}"
    echo "OpenAI API Key: ****"
    echo
    
    read -p "Bu bilgiler doğru mu? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        error "Kurulum iptal edildi."
    fi
}

# Setup GCP project
setup_gcp_project() {
    log "Google Cloud projesini yapılandırıyor..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log "Gerekli API'lar etkinleştiriliyor..."
    gcloud services enable \
        compute.googleapis.com \
        container.googleapis.com \
        sql-component.googleapis.com \
        sqladmin.googleapis.com \
        storage.googleapis.com \
        pubsub.googleapis.com \
        secretmanager.googleapis.com \
        aiplatform.googleapis.com \
        cloudbuild.googleapis.com \
        artifactregistry.googleapis.com \
        redis.googleapis.com
    
    log "API'lar etkinleştirildi ✅"
}

# Setup service accounts
setup_service_accounts() {
    log "Service account'lar oluşturuluyor..."
    
    # Terraform service account
    gcloud iam service-accounts create cofoundai-terraform \
        --description="Terraform service account for CoFound.ai" \
        --display-name="CoFound.ai Terraform" || true
    
    # Assign roles
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:cofoundai-terraform@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/editor"
    
    # Create key
    gcloud iam service-accounts keys create terraform-sa-key.json \
        --iam-account=cofoundai-terraform@$PROJECT_ID.iam.gserviceaccount.com \
        --key-file-type=json
    
    log "Service account'lar hazırlandı ✅"
}

# Setup secrets
setup_secrets() {
    log "Secret'lar oluşturuluyor..."
    
    # OpenAI API Key
    echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key \
        --data-file=- || true
    
    log "Secret'lar oluşturuldu ✅"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Terraform ile infrastructure deploy ediliyor..."
    
    cd infra
    
    # Create terraform.tfvars
    cat > terraform.tfvars <<EOF
project_id = "$PROJECT_ID"
region = "$REGION"
environment = "prod"
EOF
    
    # Initialize terraform
    terraform init
    
    # Plan
    log "Terraform plan çalıştırılıyor..."
    terraform plan -var-file=terraform.tfvars
    
    # Ask for confirmation
    read -p "Infrastructure'ı deploy etmek istiyor musunuz? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        warn "Infrastructure deployment atlandı."
        cd ..
        return
    fi
    
    # Apply
    log "Infrastructure deploy ediliyor... (Bu 10-15 dakika sürebilir)"
    terraform apply -var-file=terraform.tfvars -auto-approve
    
    # Get outputs
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    DB_IP=$(terraform output -raw database_private_ip)
    REDIS_HOST=$(terraform output -raw redis_host)
    
    cd ..
    
    log "Infrastructure deploy edildi ✅"
}

# Setup Kubernetes
setup_kubernetes() {
    log "Kubernetes cluster'a bağlanıyor..."
    
    # Get cluster credentials
    gcloud container clusters get-credentials cofoundai-cluster --region=$REGION
    
    # Create namespace
    kubectl create namespace cofoundai --dry-run=client -o yaml | kubectl apply -f -
    
    # Update deployment files
    log "Kubernetes manifests güncelliyor..."
    sed -i.bak "s/PROJECT_ID/$PROJECT_ID/g" k8s/dream-service-deployment.yaml
    sed -i.bak "s/REDIS_HOST/$REDIS_HOST/g" k8s/dream-service-deployment.yaml
    
    # Create secrets
    kubectl create secret generic database-config \
        --from-literal=host="$DB_IP" \
        --from-literal=username="cofoundai_user" \
        --from-literal=password="SecurePassword123!" \
        --from-literal=database="cofoundai" \
        --namespace=cofoundai \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log "Kubernetes hazır ✅"
}

# Build and deploy application
deploy_application() {
    log "Uygulama build ediliyor ve deploy ediliyor..."
    
    # Build docker image
    docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/cofoundai-repo/dream-service:latest \
        -f services/dream-service/Dockerfile .
    
    # Configure docker
    gcloud auth configure-docker $REGION-docker.pkg.dev
    
    # Push image
    docker push $REGION-docker.pkg.dev/$PROJECT_ID/cofoundai-repo/dream-service:latest
    
    # Deploy to Kubernetes
    kubectl apply -f k8s/dream-service-deployment.yaml -n cofoundai
    
    # Wait for deployment
    kubectl rollout status deployment/dream-service -n cofoundai --timeout=600s
    
    log "Uygulama başarıyla deploy edildi ✅"
}

# Setup CI/CD
setup_cicd() {
    log "CI/CD pipeline kuruluyor..."
    
    # Create Cloud Build trigger
    gcloud builds triggers create github \
        --name=cofoundai-main-trigger \
        --repo-name=cofoundai \
        --repo-owner=$(git config user.name) \
        --branch-pattern=main \
        --build-config=cloudbuild.yaml || true
    
    log "CI/CD pipeline hazır ✅"
}

# Get service URLs
get_service_urls() {
    log "Service URL'leri alınıyor..."
    
    # Wait for external IP
    log "External IP adresi bekleniyor... (birkaç dakika sürebilir)"
    
    for i in {1..30}; do
        EXTERNAL_IP=$(kubectl get service dream-service -n cofoundai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [[ -n "$EXTERNAL_IP" ]]; then
            break
        fi
        echo -n "."
        sleep 10
    done
    
    echo
    
    if [[ -n "$EXTERNAL_IP" ]]; then
        echo -e "${GREEN}🎉 CoFound.ai başarıyla deploy edildi!${NC}"
        echo
        echo -e "${BLUE}Service URL'leri:${NC}"
        echo "Dream Service: http://$EXTERNAL_IP/health"
        echo "API Endpoint: http://$EXTERNAL_IP/dream/process"
        echo
        echo -e "${BLUE}Test komutu:${NC}"
        echo "curl -X POST http://$EXTERNAL_IP/dream/process -H 'Content-Type: application/json' -d '{\"project_description\": \"Test todo app\", \"user_id\": \"test\"}'"
    else
        warn "External IP henüz atanmadı. Şu komutla kontrol edebilirsiniz:"
        echo "kubectl get service dream-service -n cofoundai"
    fi
}

# Cleanup function
cleanup() {
    log "Cleanup işlemleri..."
    # Remove temporary files
    rm -f terraform-sa-key.json
    rm -f k8s/*.bak
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "======================================"
    echo "  CoFound.ai GCP Setup Script v1.0    "
    echo "======================================"
    echo -e "${NC}"
    
    check_prerequisites
    get_user_input
    setup_gcp_project
    setup_service_accounts
    setup_secrets
    deploy_infrastructure
    setup_kubernetes
    deploy_application
    setup_cicd
    get_service_urls
    cleanup
    
    echo
    echo -e "${GREEN}🚀 CoFound.ai başarıyla Google Cloud Platform'da kuruldu!${NC}"
    echo
    echo -e "${BLUE}Sonraki adımlar:${NC}"
    echo "1. Domain name ayarlayın (isteğe bağlı)"
    echo "2. SSL certificate kurun"
    echo "3. Monitoring dashboard'ları kontrol edin"
    echo "4. Backup stratejisi oluşturun"
    echo
    echo -e "${YELLOW}Daha fazla bilgi için: docs/GCP-DEPLOYMENT-GUIDE.md${NC}"
}

# Trap for cleanup on exit
trap cleanup EXIT

# Run main function
main "$@" 