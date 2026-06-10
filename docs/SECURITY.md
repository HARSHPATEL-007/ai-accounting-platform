# Security Policy

## Data Protection

### Encryption
- **At Rest**: AES-256 (PostgreSQL TDE, S3 SSE-KMS, Redis encryption)
- **In Transit**: TLS 1.3, mTLS between microservices
- **Key Management**: AWS KMS with 90-day rotation, HashiCorp Vault for secrets

### PII Handling
- **Detection**: Microsoft Presidio for PAN, Aadhaar, bank accounts
- **Tokenization**: Format-Preserving Encryption before LLM context
- **Anonymization**: Replace with `<ENTITY_TYPE>` tokens
- **Consent**: Explicit consent per DPDP Act 2023

### Access Control
- **Authentication**: OAuth 2.0 + OIDC, MFA (TOTP/Biometric)
- **Authorization**: RBAC + ABAC, Row-Level Security in PostgreSQL
- **Audit**: Immutable logs with SHA-256 chain, WORM storage

## AI Safety

### Guardrails
1. **Topical**: Block non-accounting queries (crypto trading, illegal content)
2. **Hallucination**: Verify citations, cross-check numerical values
3. **Execution**: Prevent autonomous filing, transfers, modifications

### Model Security
- Local models (Llama-3/Mistral) for PII-sensitive workloads
- LiteLLM proxy for unified API with fallback routing
- Token cost tracking per client

## Infrastructure Security

### Network
- VPC with private subnets, NAT Gateways
- AWS PrivateLink/GCP VPC-SC for service communication
- Network Policies (zero-trust) in Kubernetes
- WAF with OWASP Top 10 rules

### Container Security
- Distroless base images
- Non-root user execution
- Read-only root filesystems
- Vulnerability scanning (Trivy/Snyk) in CI/CD

## Incident Response

1. **Detection**: PagerDuty alerts for guardrails block rate > 5%, token cost spikes
2. **Containment**: Automatic scaling isolation, circuit breakers
3. **Investigation**: LangSmith trace replay for every AI response
4. **Recovery**: Rollback via Terraform, database point-in-time recovery

## Compliance

- **DPDP Act 2023**: Data minimization, purpose limitation, consent
- **SOC 2 Type II**: Access controls, change management, monitoring
- **ISO 27001**: Risk assessment, security policies, training
- **RBI Guidelines**: Account Aggregator consent framework
- **GSTN**: Secure API integration with certificate pinning

## Reporting Vulnerabilities

Email: security@accounting-platform.in
PGP Key: [Available on request]
Response Time: 24 hours for critical, 72 hours for high
