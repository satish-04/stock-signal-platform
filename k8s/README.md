# Stock Signal App - Kubernetes Deployment

This directory contains Kubernetes manifests and Helm charts for deploying the Stock Signal App to a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.x
- kubectl configured with cluster access
- Docker registry accessible from the cluster (for pulling images)

## Quick Start

### Using Helm (Recommended)

```bash
# Add the repository (if using a remote chart)
helm repo add stock-signal-app https://your-helm-repo.com
helm repo update

# Install with default values
helm install stock-signal-app ./charts \
  --namespace stock-signal-app \
  --create-namespace

# Install with production values
helm install stock-signal-app ./charts \
  --namespace stock-signal-app \
  --create-namespace \
  -f ./charts/values-prod.yaml

# Upgrade the deployment
helm upgrade stock-signal-app ./charts \
  --namespace stock-signal-app \
  -f ./charts/values-prod.yaml

# Uninstall
helm uninstall stock-signal-app --namespace stock-signal-app
```

### Using Kubernetes Manifests

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get all -n stock-signal-app
kubectl get pods -n stock-signal-app

# View logs
kubectl logs -f deployment/stock-signal-app-backend -n stock-signal-app
kubectl logs -f deployment/stock-signal-app-frontend -n stock-signal-app

# Port-forward for local testing
kubectl port-forward svc/stock-signal-app-frontend 3000:3000 -n stock-signal-app
kubectl port-forward svc/stock-signal-app-backend 8000:8000 -n stock-signal-app
```

## Configuration

### Environment Variables

Key environment variables that can be configured:

- `PYTHONUNBUFFERED=1` - Python output logging
- `TRADING_MODE=paper` - Set to 'live' for actual trading (disable by default)
- `MARKET_DATA_MODE=mock` - Set to 'real' for real market data
- `ENABLE_ORDER_SUBMISSION=false` - Must be set to 'true' for live trading

### Secrets Management

Secrets should be managed using one of these approaches:

1. **Kubernetes Secrets** (simple)
   ```bash
   kubectl create secret generic stock-signal-app-secrets \
     --from-literal=ANTHROPIC_API_KEY=sk-... \
     --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
     --namespace stock-signal-app
   ```

2. **External Secrets Operator** (recommended for production)
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: stock-signal-app-secrets
   spec:
     secretStoreRef:
       name: aws-secrets-manager
     data:
       - secretKey: ANTHROPIC_API_KEY
         remoteRef:
           key: stock-signal-app/prod
           property: anthropic/api_key
   ```

3. **Vault Integration** (enterprise)
   ```yaml
   apiVersion: secrets-store.csi.x-k8s.io/v1
   kind: SecretProviderClass
   metadata:
     name: vault-secrets
   spec:
     provider: vault
     parameters:
       objects: |
         - objectName: "secret/data/stock-signal-app"
           secretPath: "secret/data/stock-signal-app"
   ```

## Monitoring

### Prometheus Metrics

The application exposes metrics at `/metrics` endpoint. Enable scraping by applying the ServiceMonitor manifest:

```bash
kubectl apply -f k8s/monitoring.yaml
```

### Grafana Dashboard

A pre-built Grafana dashboard is available in `charts/templates/monitoring.yaml`. Key metrics:

- CPU usage by service
- Memory usage by container
- HTTP request rate by status code
- Error rates

## Production Checklist

Before deploying to production:

1. **Security**
   - [ ] Use external secrets manager (Vault/AWS Secrets Manager)
   - [ ] Enable TLS/HTTPS
   - [ ] Configure network policies
   - [ ] Set up RBAC properly
   - [ ] Disable unnecessary ports

2. **Reliability**
   - [ ] Configure pod disruption budgets
   - [ ] Set up anti-affinity rules
   - [ ] Enable horizontal pod autoscaling
   - [ ] Configure proper resource limits

3. **Observability**
   - [ ] Set up logging aggregation
   - [ ] Configure alerting rules
   - [ ] Setup tracing (Jaeger/Zipkin)

4. **Data**
   - [ ] Backup PostgreSQL database
   - [ ] Configure Redis persistence
   - [ ] Set up volume snapshots

## Troubleshooting

### Common Issues

1. **Pods CrashLooping**
   ```bash
   kubectl logs <pod-name> -n stock-signal-app --previous
   ```

2. **Services Not Reachable**
   ```bash
   kubectl describe service <service-name> -n stock-signal-app
   ```

3. **Database Connection Failed**
   ```bash
   kubectl exec -it <pod-name> -n stock-signal-app -- nc -zv db 5432
   ```

### Debugging Commands

```bash
# Get events
kubectl get events -n stock-signal-app --sort-by='.lastTimestamp'

# Describe resources
kubectl describe deployment <deployment-name> -n stock-signal-app
kubectl describe pod <pod-name> -n stock-signal-app

# Exec into container
kubectl exec -it <pod-name> -n stock-signal-app -- /bin/sh

# Check health endpoints
kubectl port-forward svc/stock-signal-app-backend 8000:8000 -n stock-signal-app
curl http://localhost:8000/health
```

## CI/CD Integration

The project includes a GitHub Actions workflow at `.github/workflows/ci-cd.yml` that:

1. Runs Python linting and tests
2. Runs frontend linting
3. Builds Docker images
4. Pushes to container registry
5. Deploys to Kubernetes on main branch commits

To use the CI/CD:

1. Store your kubeconfig as a GitHub secret: `KUBE_CONFIG`
2. Store your Kubernetes context name as: `KUBERNETES_CONTEXT`
3. Add secrets for external services (Vault/Secrets Manager credentials)
4. Push to the `main` branch to trigger deployment

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment/stock-signal-app-backend --replicas=3 -n stock-signal-app

# Scale frontend
kubectl scale deployment/stock-signal-app-frontend --replicas=3 -n stock-signal-app
```

### Automatic Scaling

The Helm chart includes HorizontalPodAutoscaler resources that scale based on CPU utilization. Adjust in `values.yaml`:

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

## Maintenance

### Database Migration

```bash
# Run migrations
kubectl exec -it deployment/stock-signal-app-backend -n stock-signal-app \
  -- python -m app.db.migrate

# Backup database
kubectl exec -it deployment/stock-signal-app-backend -n stock-signal-app \
  -- pg_dump -U stock_signal stock_signal > backup.sql
```

### Rolling Restart

```bash
# Perform rolling restart
kubectl rollout restart deployment/stock-signal-app-backend -n stock-signal-app
kubectl rollout restart deployment/stock-signal-app-frontend -n stock-signal-app

# Check rollout status
kubectl rollout status deployment/stock-signal-app-backend -n stock-signal-app
```