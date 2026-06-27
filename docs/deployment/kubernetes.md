# Kubernetes / Helm Deployment

## Prerequisites

- Kubernetes 1.28+
- Helm 3.12+
- `kubectl` connected to your cluster
- External PostgreSQL (RDS, Cloud SQL, or managed)
- External Redis (ElastiCache, Upstash, or managed)
- External S3-compatible storage (AWS S3, GCS, or MinIO in distributed mode)
- AWS Bedrock access in your target region
- Stripe account with configured products

---

## 1. Add required Secrets

Create Kubernetes Secrets before installing the chart. The chart references
these by name via `values.yaml`.

```bash
# JWT signing secret
kubectl create secret generic openidp-jwt \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)"

# Database credentials
kubectl create secret generic openidp-db-credentials \
  --from-literal=DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/openidp"

# Redis
kubectl create secret generic openidp-redis-credentials \
  --from-literal=REDIS_URL="rediss://user:pass@host:6380/0"

# MinIO / S3
kubectl create secret generic openidp-minio-credentials \
  --from-literal=MINIO_ENDPOINT="s3.amazonaws.com" \
  --from-literal=MINIO_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE" \
  --from-literal=MINIO_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" \
  --from-literal=MINIO_SECURE="true"

# AWS Bedrock
kubectl create secret generic openidp-aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE" \
  --from-literal=AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/..."

# Stripe
kubectl create secret generic openidp-stripe-credentials \
  --from-literal=STRIPE_SECRET_KEY="sk_live_..." \
  --from-literal=STRIPE_WEBHOOK_SECRET="whsec_..."
```

---

## 2. Configure values

Create a `values.override.yaml` with your environment-specific settings:

```yaml
api:
  image:
    repository: ghcr.io/your-org/openidp-api
    tag: "1.0.0"
  env:
    ENVIRONMENT: production
    ALLOWED_ORIGINS: "https://app.yourcompany.com"
    FRONTEND_URL: "https://app.yourcompany.com"
    STRIPE_PRICE_STARTER: "price_xxxxx"
    STRIPE_PRICE_PROFESSIONAL: "price_yyyyy"
    BEDROCK_MODEL_ID: "us.anthropic.claude-sonnet-4-6"

web:
  image:
    repository: ghcr.io/your-org/openidp-web
    tag: "1.0.0"
  env:
    NEXT_PUBLIC_API_URL: "https://app.yourcompany.com"
    NEXT_PUBLIC_WS_URL: "wss://app.yourcompany.com"

ocrEngine:
  image:
    repository: ghcr.io/your-org/openidp-ocr-engine
    tag: "1.0.0"
    target: cpu  # or 'gpu' for GPU nodes

ingress:
  hosts:
    - host: app.yourcompany.com
      paths:
        - path: /api
          service: api
        - path: /ws
          service: api
        - path: /
          service: web
  tls:
    - secretName: openidp-tls
      hosts:
        - app.yourcompany.com

secrets:
  jwt: openidp-jwt
  postgresql: openidp-db-credentials
  redis: openidp-redis-credentials
  minio: openidp-minio-credentials
  aws: openidp-aws-credentials
  stripe: openidp-stripe-credentials
```

---

## 3. Install the chart

```bash
helm install openidp ./infra/helm/openidp \
  -f infra/helm/openidp/values.production.yaml \
  -f values.override.yaml \
  --namespace openidp \
  --create-namespace
```

---

## 4. Run database migrations

```bash
kubectl run alembic-migrate \
  --image=ghcr.io/your-org/openidp-api:1.0.0 \
  --restart=Never \
  --namespace=openidp \
  --env="DATABASE_URL=$(kubectl get secret openidp-db-credentials -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
  -- uv run alembic upgrade head

kubectl wait --for=condition=complete pod/alembic-migrate --timeout=120s --namespace=openidp
kubectl delete pod alembic-migrate --namespace=openidp
```

---

## 5. Download OCR models to the cluster

The OCR engine expects models at `/app/models`. Use an init container or a
one-time Job to populate the persistent volume:

```yaml
# infra/k8s/ocr-model-init-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: ocr-model-init
  namespace: openidp
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: downloader
          image: python:3.12-slim
          command: ["/bin/bash", "-c"]
          args:
            - |
              apt-get update -q && apt-get install -y curl tar
              bash /scripts/download_models.sh /models
          volumeMounts:
            - name: ocr-models
              mountPath: /models
            - name: scripts
              mountPath: /scripts
      volumes:
        - name: ocr-models
          persistentVolumeClaim:
            claimName: openidp-ocr-models-pvc
        - name: scripts
          configMap:
            name: openidp-scripts
```

```bash
kubectl apply -f infra/k8s/ocr-model-init-job.yaml
kubectl wait --for=condition=complete job/ocr-model-init --timeout=300s --namespace=openidp
```

---

## 6. Verify the deployment

```bash
# Check all pods are Running
kubectl get pods --namespace=openidp

# API health
kubectl port-forward svc/openidp-api 8000:8000 --namespace=openidp &
curl http://localhost:8000/api/health

# Check worker logs
kubectl logs -l app.kubernetes.io/component=worker --namespace=openidp --tail=50
```

---

## Scaling

### Worker scaling (queue-based HPA)

The worker HPA uses both CPU utilization and a custom Redis queue-depth metric.
Install KEDA for queue-depth-based scaling:

```bash
helm install keda kedacore/keda --namespace keda --create-namespace
```

Then apply the ScaledObject:
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: openidp-worker-scaler
  namespace: openidp
spec:
  scaleTargetRef:
    name: openidp-worker
  minReplicaCount: 3
  maxReplicaCount: 20
  triggers:
    - type: redis
      metadata:
        address: redis-host:6379
        listName: arq:queue:pipeline
        listLength: "5"
```

### GPU OCR scaling

Enable GPU support in values:
```yaml
ocrEngine:
  image:
    target: gpu
  gpu:
    enabled: true
    nodeSelector:
      accelerator: nvidia-tesla-t4
    tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

---

## Upgrade

```bash
helm upgrade openidp ./infra/helm/openidp \
  -f infra/helm/openidp/values.production.yaml \
  -f values.override.yaml \
  --namespace openidp

# Then run migrations if the new version includes schema changes
kubectl run alembic-migrate ... (see step 4)
```

## Rollback

```bash
helm rollback openidp --namespace openidp
```
