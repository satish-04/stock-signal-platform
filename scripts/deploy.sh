#!/bin/bash

# Deployment script for Stock Signal App
set -e

echo "🚀 Stock Signal App Deployment Script"
echo "====================================="

# Parse command line arguments
DEPLOY_ENV="${1:-dev}"
HELM_INSTALL="${2:-true}"

# Configuration
NAMESPACE="stock-signal-app"
CHART_PATH="./charts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}INFO:${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}WARN:${NC} $1"
}

log_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

# Validate prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl."
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed. Please install Helm 3."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to a Kubernetes cluster. Please run 'kubectl cluster-info'."
        exit 1
    fi
    
    log_info "Prerequisites satisfied."
}

# Login to Docker registry
login_to_registry() {
    log_info "Logging in to Docker registry..."
    
    if [ -z "$DOCKER_REGISTRY" ]; then
        log_warn "DOCKER_REGISTRY not set. Using ghcr.io"
        DOCKER_REGISTRY="ghcr.io"
    fi
    
    if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
        log_warn "Docker credentials not provided. Using local registry."
    else
        echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" --username "$DOCKER_USERNAME" --password-stdin
    fi
    
    log_info "Docker login complete."
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Backend image
    docker build -t "$DOCKER_REGISTRY/$NAMESPACE/backend:latest" .
    
    # Frontend image
    docker build -t "$DOCKER_REGISTRY/$NAMESPACE/frontend:latest" ./frontend
    
    # Tag images for deployment
    docker tag "$DOCKER_REGISTRY/$NAMESPACE/backend:latest" "$DOCKER_REGISTRY/$NAMESPACE/backend:$DEPLOY_ENV"
    docker tag "$DOCKER_REGISTRY/$NAMESPACE/frontend:latest" "$DOCKER_REGISTRY/$NAMESPACE/frontend:$DEPLOY_ENV"
    
    log_info "Docker images built successfully."
}

# Push Docker images
push_images() {
    log_info "Pushing Docker images to registry..."
    
    docker push "$DOCKER_REGISTRY/$NAMESPACE/backend:$DEPLOY_ENV"
    docker push "$DOCKER_REGISTRY/$NAMESPACE/frontend:$DEPLOY_ENV"
    
    log_info "Docker images pushed successfully."
}

# Create namespace
create_namespace() {
    log_info "Creating namespace $NAMESPACE..."
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Namespace created/verified."
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."
    
    # Generate secure random keys
    SECRET_KEY=$(openssl rand -hex 32)
    ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-sk-placeholder-$(openssl rand -hex 16)}"
    
    # Create secrets
    kubectl create secret generic stock-signal-app-secrets \
        --from-literal=SECRET_KEY="$SECRET_KEY" \
        --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        --from-literal=DB_HOST="stock-signal-app-postgresql.$NAMESPACE.svc.cluster.local" \
        --from-literal=DB_PORT="5432" \
        --from-literal=DB_USER="stock_signal" \
        --from-literal=DB_NAME="stock_signal_prod" \
        --from-literal=REDIS_HOST="stock-signal-app-redis.$NAMESPACE.svc.cluster.local" \
        --from-literal=REDIS_PORT="6379" \
        --from-literal=DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Secrets created successfully."
}

# Deploy with Helm
deploy_helm() {
    log_info "Deploying with Helm..."
    
    # Update Helm repositories
    helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
    helm repo update
    
    # Install/Upgrade the chart
    if [ "$HELM_INSTALL" = "true" ]; then
        helm upgrade --install \
            stock-signal-app \
            "$CHART_PATH" \
            --namespace "$NAMESPACE" \
            --create-namespace \
            -f "$CHART_PATH/values-prod.yaml" \
            --set image.repository="$DOCKER_REGISTRY/$NAMESPACE/backend" \
            --set image.tag="$DEPLOY_ENV" \
            --set frontendImage.repository="$DOCKER_REGISTRY/$NAMESPACE/frontend" \
            --set frontendImage.tag="$DEPLOY_ENV" \
            --wait \
            --timeout 10m
    else
        log_info "Skipping Helm install (--helm-install=false)"
    fi
    
    log_info "Helm deployment complete."
}

# Deploy with Kubernetes manifests
deploy_manifests() {
    log_info "Deploying with Kubernetes manifests..."
    
    # Apply namespace
    kubectl apply -f "$CHART_PATH/../k8s/namespace.yaml"
    
    # Apply secrets
    kubectl apply -f "$CHART_PATH/../k8s/secret.yaml"
    
    # Apply databases
    kubectl apply -f "$CHART_PATH/../k8s/postgres-deployment.yaml"
    kubectl apply -f "$CHART_PATH/../k8s/redis-deployment.yaml"
    
    # Apply backend
    kubectl apply -f "$CHART_PATH/../k8s/backend-deployment.yaml"
    
    # Apply frontend
    kubectl apply -f "$CHART_PATH/../k8s/frontend-deployment.yaml"
    
    # Apply worker
    kubectl apply -f "$CHART_PATH/../k8s/worker-deployment.yaml"
    
    # Apply ingress
    kubectl apply -f "$CHART_PATH/../k8s/ingress.yaml"
    
    log_info "Kubernetes manifests deployed successfully."
}

# Wait for deployment
wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    # Wait for pods
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=stock-signal-app \
        --namespace "$NAMESPACE" \
        --timeout=300s
    
    # Get pod status
    kubectl get pods -n "$NAMESPACE"
    
    log_info "Deployment verification complete."
}

# Display deployment info
show_deployment_info() {
    echo ""
    log_info "====================================="
    log_info "Deployment Complete!"
    log_info "====================================="
    
    # Get external IP if LoadBalancer
    INGRESS_IP=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "N/A")
    
    # Get services
    BACKEND_SVC=$(kubectl get svc stock-signal-app-backend -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "N/A")
    FRONTEND_SVC=$(kubectl get svc stock-signal-app-frontend -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "N/A")
    
    echo ""
    log_info "Service Endpoints:"
    echo "  Backend:  $BACKEND_SVC:8000"
    echo "  Frontend: $FRONTEND_SVC:3000"
    echo "  Ingress IP: $INGRESS_IP"
    
    echo ""
    log_info "Next Steps:"
    echo "  1. Update DNS record to point to ingress IP"
    echo "  2. Configure TLS certificate"
    echo "  3. Update trading_mode to 'live' when ready"
    
    # Show logs command
    echo ""
    log_info "View logs with:"
    echo "  kubectl logs -f deployment/stock-signal-app-backend -n $NAMESPACE"
    echo "  kubectl logs -f deployment/stock-signal-app-frontend -n $NAMESPACE"
}

# Cleanup function
cleanup() {
    log_info "Performing cleanup..."
    
    # Remove temporary files
    rm -f /tmp/stock-signal-app-secrets.yaml
    
    log_info "Cleanup complete."
}

# Main deployment function
deploy() {
    check_prerequisites
    
    case "$DEPLOY_ENV" in
        dev)
            log_info "Deploying to development environment..."
            create_namespace
            create_secrets
            deploy_manifests
            wait_for_deployment
            show_deployment_info
            ;;
        staging|prod)
            login_to_registry
            build_images
            push_images
            create_namespace
            create_secrets
            deploy_helm
            wait_for_deployment
            show_deployment_info
            ;;
        *)
            log_error "Invalid environment: $DEPLOY_ENV"
            log_info "Valid environments: dev, staging, prod"
            exit 1
            ;;
    esac
}

# Rollback function
rollback() {
    log_info "Rolling back to previous deployment..."
    
    kubectl rollout undo deployment/stock-signal-app-backend -n "$NAMESPACE"
    kubectl rollout undo deployment/stock-signal-app-frontend -n "$NAMESPACE"
    
    log_info "Rollback complete."
}

# Scale function
scale() {
    COMPONENT="${1:-all}"
    REPLICAS="${2:-2}"
    
    log_info "Scaling $COMPONENT to $REPLICAS replicas..."
    
    case "$COMPONENT" in
        all)
            kubectl scale deployment/stock-signal-app-backend --replicas="$REPLICAS" -n "$NAMESPACE"
            kubectl scale deployment/stock-signal-app-frontend --replicas="$REPLICAS" -n "$NAMESPACE"
            ;;
        backend)
            kubectl scale deployment/stock-signal-app-backend --replicas="$REPLICAS" -n "$NAMESPACE"
            ;;
        frontend)
            kubectl scale deployment/stock-signal-app-frontend --replicas="$REPLICAS" -n "$NAMESPACE"
            ;;
        *)
            log_error "Invalid component: $COMPONENT"
            exit 1
            ;;
    esac
    
    log_info "Scale complete."
}

# Show usage
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  deploy [environment]  Deploy to environment (dev/staging/prod)"
    echo "  rollback              Rollback to previous deployment"
    echo "  scale <component> <n> Scale component to n replicas"
    echo ""
    echo "Examples:"
    echo "  $0 deploy dev         # Deploy to development"
    echo "  $0 deploy prod        # Deploy to production"
    echo "  $0 rollback           # Rollback latest deployment"
    echo "  $0 scale all 3        # Scale all components to 3 replicas"
}

# Main entry point
case "${1:-}" in
    deploy)
        shift
        DEPLOY_ENV="${1:-dev}"
        helm_install="${2:-true}"
        deploy
        ;;
    rollback)
        rollback
        ;;
    scale)
        shift
        COMPONENT="${1:-all}"
        REPLICAS="${2:-2}"
        scale "$COMPONENT" "$REPLICAS"
        ;;
    helm)
        # Direct Helm deployment
        shift
        check_prerequisites
        create_namespace
        deploy_helm
        show_deployment_info
        ;;
    *)
        usage
        exit 1
        ;;
esac

# Cleanup on exit
trap cleanup EXIT