# Deployment Guide

## Environments

| Environment | Purpose | Infrastructure |
|-------------|---------|---------------|
| Local | Development | Docker Compose |
| Staging | Integration testing | EKS/GKE (single AZ) |
| Production | Live traffic | EKS/GKE (multi-AZ, multi-region DR) |

## Deployment Pipeline

```mermaid
graph LR
    A[Developer Push] --> B[GitHub Actions]
    B --> C[Unit Tests]
    C --> D[Integration Tests]
    D --> E[Security Scan]
    E --> F[Build Container]
    F --> G[Push to ECR]
    G --> H[Deploy to Staging]
    H --> I[E2E Tests]
    I --> J[Deploy to Production]
    J --> K[Smoke Tests]
    K --> L[Traffic Shift]
```

## CI/CD Configuration

### GitHub Actions Workflow
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pytest ai-orchestrator/tests
          go test ./ledger-processor/...
          npm test --prefix web-dashboard

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'

  build-and-deploy:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
          aws-region: ap-south-1

      - name: Build and push images
        run: |
          docker build -t $ECR/ai-orchestrator:$GITHUB_SHA ai-orchestrator/
          docker push $ECR/ai-orchestrator:$GITHUB_SHA

      - name: Deploy to EKS
        run: |
          kubectl set image deployment/ai-orchestrator ai-orchestrator=$ECR/ai-orchestrator:$GITHUB_SHA -n accounting-platform
          kubectl rollout status deployment/ai-orchestrator -n accounting-platform
```

## Database Migrations

### Using golang-migrate (Go services)
```bash
migrate -path ledger-processor/migrations -database "postgres://user:pass@host/db" up
```

### Using Alembic (Python services)
```bash
cd ai-orchestrator
alembic upgrade head
```

## Rollback Procedures

### Service Rollback
```bash
# Rollback to previous version
kubectl rollout undo deployment/ai-orchestrator -n accounting-platform

# Verify rollback
kubectl get pods -n accounting-platform
```

### Database Rollback
```bash
# Point-in-time recovery (PITR)
aws rds restore-db-instance-to-point-in-time \
    --source-db-instance accounting-platform-prod \
    --target-db-instance accounting-platform-prod-rollback \
    --restore-time 2024-06-01T12:00:00Z
```

## Monitoring & Alerting

### Key Metrics
- RAG retrieval latency (p95 < 2s)
- Guardrails block rate (< 5%)
- Token cost per client (daily budget)
- STP success rate (> 90%)
- First-Pass Acceptance Rate (> 85%)

### Alert Channels
- PagerDuty: Critical alerts (latency, errors, security)
- Slack: Warnings and deployment notifications
- Email: Daily cost reports

## Capacity Planning

### Peak Season Scaling (July ITR, Monthly GST)
- Pre-scale to 2x baseline 1 week before deadline
- KEDA scheduled scalers for predictable peaks
- Database read replicas for reporting queries
- CDN caching for static assets

### Resource Limits
| Service | Baseline | Peak | Max |
|---------|----------|------|-----|
| AI Orchestrator | 3 pods | 10 pods | 20 pods |
| Ledger Processor | 5 pods | 15 pods | 50 pods |
| OCR Pipeline | 2 pods | 8 pods | 20 pods |
| PostgreSQL | db.r6g.xlarge | db.r6g.2xlarge | db.r6g.4xlarge |

## Disaster Recovery

### RPO/RTO
- **RPO**: 1 hour (continuous backup to S3)
- **RTO**: 4 hours (automated failover to DR region)

### DR Region
- Primary: ap-south-1 (Mumbai)
- DR: ap-south-2 (Hyderabad)
- Async replication for PostgreSQL
- S3 cross-region replication for documents
