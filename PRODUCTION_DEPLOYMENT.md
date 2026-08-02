# Stock Signal App - Production Deployment Guide

## Overview

This guide covers deploying the Stock Signal App to production using Kubernetes and Helm.

## Architecture

```
                    Internet
                         │
                  ┌──────▼──────┐
                  │   Ingress   │
                  │    (TLS)    │
                  └──────┬──────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   Frontend          Backend           Worker
  (React)         (FastAPI)        (Background)
    Port:3000       Port:8000
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
      PostgreSQL                   Redis
     (Primary DB)              (Cache/Queues)
```

## Prerequisites

### Tools
- Kubernetes 1.24+ cluster (EKS/GKE/AKS)
- Helm 3.x
- kubectl configured with admin access
- Docker registry accessible from cluster

### Credentials
- Database credentials (PostgreSQL)
- IBKR API credentials
- Anthropic API key for Claude AI

## Quick Start

### 1. Prepare Your Environment

```bash
# Clone the repository
git clone https://github.com/your-org/stock-signal-app.git
cd stock-signal-app

# Set environment variables
export KUBECONFIG=path/to/your/kubeconfig
```

### 2. Configure Secrets

Create a `secrets.yaml` file:

```yaml
# secrets.yaml
ANTHROPIC_API_KEY: sk-ant-api01-your-key-here
IB_API_CLIENT_ID: your-ibkr-client-id
IB_API_SECRET: your-ibkr-secret
SECRET_KEY: $(openssl rand -hex 32)
DJANGO_ALLOWED_HOSTS: stock-signal-app.example.com
```

### 3. Deploy with Helm

```bash
# Add bitnami repo for dependencies
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Create namespace
kubectl create namespace stock-signal-app

# Deploy
helm upgrade --install stock-signal-app ./charts \
  --namespace stock-signal-app \
  -f ./charts/values-prod.yaml \
  --set secrets.anthropicApiKey=sk-ant-api01-your-key \
  --set secrets.secretKey=$(openssl rand -hex 32) \
  --wait --timeout 10m
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n stock-signal-app

# Check services
kubectl get svc -n stock-signal-app

# Check ingress
kubectl get ingress -n stock-signal-app

# View logs
kubectl logs -f deployment/stock-signal-app-backend -n stock-signal-app
```

## Deployment Methods

### Method 1: Helm (Recommended)

```bash
# Deploy to development
helm upgrade --install stock-signal-app ./charts \
  --namespace stock-signal-app \
  -f ./charts/values.yaml

# Deploy to production
helm upgrade --install stock-signal-app ./charts \
  --namespace stock-signal-app \
  -f ./charts/values-prod.yaml
```

### Method 2: Manual Manifests

```bash
# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets
kubectl create secret generic stock-signal-app-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-... \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply all manifests
kubectl apply -f k8s/
```

### Method 3: Deploy Script

```bash
# Make script executable
chmod +x scripts/deploy.sh

# Deploy to development
./scripts/deploy.sh deploy dev

# Deploy to production
./scripts/deploy.sh deploy prod
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADING_MODE` | paper | Set to 'live' for actual trading |
| `MARKET_DATA_MODE` | mock | Set to 'real' for live market data |
| `ENABLE_ORDER_SUBMISSION` | false | Enable order submission to broker |
| `PYTHONUNBUFFERED` | 1 | Python output logging |

### Production Checklist

#### Security
- [ ] TLS/HTTPS enabled for ingress
- [ ] External secrets manager configured (Vault/AWS Secrets Manager)
- [ ] Network policies in place
- [ ] RBAC properly configured
- [ ] Secrets rotated regularly

#### Reliability
- [ ] Database backups configured
- [ ] Horizontal Pod Autoscaler enabled
- [ ] Pod disruption budgets set
- [ ] Anti-affinity rules configured

#### Monitoring
- [ ] Prometheus metrics scraping enabled
- [ ] Grafana dashboard configured
- [ ] Alerting rules defined
- [ ] Log aggregation set up

## Scaling

### Automatic Scaling (via Helm)

Edit `charts/values-prod.yaml`:

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment/stock-signal-app-backend \
  --replicas=3 -n stock-signal-app

# Scale frontend
kubectl scale deployment/stock-signal-app-frontend \
  --replicas=3 -n stock-signal-app
```

## Monitoring

### Metrics Endpoint

The application exposes Prometheus metrics at:
- Backend: `http://localhost:8000/metrics`
- Frontend: `http://localhost:3000/metrics`

### Grafana Dashboard

Import the dashboard from `charts/templates/monitoring.yaml` or use:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-stock-signal-app
data:
  stock-signal-app.json: |
    <dashboard JSON>
```

## CI/CD Integration

### GitHub Actions Workflow

The project includes `.github/workflows/ci-cd.yml` which:

1. Runs Python linting and tests
2. Lints frontend code
3. Builds Docker images
4. Pushes to registry
5. Deploys to Kubernetes on `main` branch

### Configure Secrets in GitHub

1. Go to repository Settings > Secrets and variables > Actions
2. Add `KUBE_CONFIG` (base64-encoded kubeconfig)
3. Add `KUBERNETES_CONTEXT` (cluster context name)
4. Add `ANTHROPIC_API_KEY`

## Troubleshooting

### Common Issues

1. **Pods CrashLooping**
   ```bash
   kubectl logs <pod-name> -n stock-signal-app --previous
   ```

2. **Database Connection Failed**
   ```bash
   kubectl exec -it <pod-name> -n stock-signal-app \
     -- nc -zv stock-signal-app-postgresql 5432
   ```

3. **Ingress Not Working**
   ```bash
   kubectl describe ingress stock-signal-app-ingress -n stock-signal-app
   ```

### Debug Commands

```bash
# Get events
kubectl get events -n stock-signal-app --sort-by='.lastTimestamp'

# Describe resources
kubectl describe deployment <name> -n stock-signal-app

# Exec into container
kubectl exec -it <pod-name> -n stock-signal-app -- /bin/sh

# Port-forward for local testing
kubectl port-forward svc/stock-signal-app-frontend 3000:3000 -n stock-signal-app
```

## Maintenance

### Database Migration

```bash
kubectl exec -it deployment/stock-signal-app-backend \
  -- python -m app.db.migrate
```

### Backup Database

```bash
kubectl exec -it deployment/stock-signal-app-backend \
  -- pg_dump -U stock_signal stock_signal_prod > backup.sql
```

### Rolling Restart

```bash
kubectl rollout restart deployment/stock-signal-app-backend -n stock-signal-app
kubectl rollout restart deployment/stock-signal-app-frontend -n stock-signal-app

kubectl rollout status deployment/stock-signal-app-backend -n stock-signal-app
```

### Update Configuration

```bash
# Edit deployment
kubectl edit deployment stock-signal-app-backend -n stock-signal-app

# Or apply new manifests
kubectl apply -f k8s/backend-deployment.yaml --namespace stock-signal-app
```

## Security Best Practices

1. **Secrets Management**
   - Use external secrets manager (Vault/Secrets Manager)
   - Rotate secrets regularly
   - Never commit secrets to repository

2. **Network Security**
   - Enable TLS for all services
   - Configure network policies
   - Use private subnets for databases

3. **Access Control**
   - Implement RBAC properly
   - Use service accounts instead of cluster-admin
   - Enable audit logging

4. **Trades Safety**
   - Keep `TRADING_MODE=paper` until fully tested
   - Set up trading limits and kill switches
   - Enable comprehensive logging for all trades

## Cost Optimization

1. **Resource Quotas**
   ```yaml
   resources:
     limits:
       cpu: "1"
       memory: 2Gi
     requests:
       cpu: "500m"
       memory: 1Gi
   ```

2. **Auto-scaling**
   - Enable HPA to scale based on load
   - Set appropriate min/max replicas

3. **Spot Instances**
   - Use spot instances for non-critical workloads
   - Configure preemptible nodes for workers

## Next Steps

After successful deployment:

1. Configure DNS to point to your ingress
2. Set up SSL certificate (Let's Encrypt or AWS ACM)
3. Configure monitoring and alerting
4. Enable real trading mode (only after thorough testing)
5. Set up automated backups

## Support

For issues:
1. Check logs: `kubectl logs <pod-name> -n stock-signal-app`
2. Check events: `kubectl get events -n stock-signal-app --sort-by='.lastTimestamp'`
3. Review documentation in `docs/`

## References

- Kubernetes: https://kubernetes.io/docs/
- Helm: https://helm.sh/docs/
- Prometheus: https://prometheus.io/docs/introduction/overview/
- Grafana: https://grafana.com/docs/