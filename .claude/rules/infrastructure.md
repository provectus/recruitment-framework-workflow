---
globs:
  - "infra/**"
---

- Project name in infra is `lauter` — all AWS resources prefixed `lauter-*` (cluster, service, ECR, SSM paths)
- Terraform ~1.14.5 + AWS provider ~6.33 — no TLS provider; OIDC thumbprint managed by AWS server-side
- `default_tags` at provider level sets `Project`, `Environment`, `ManagedBy` — do NOT add these in per-resource `tags` blocks (only `Name` + functional tags like `Type`)
- State backend is manual — S3 bucket + DynamoDB table must be created before `terraform init` (see `infra/ROLLOUT.md`)
- `terraform.tfvars` is gitignored — copy from `terraform.tfvars.example`, never commit
- ECS images use `:latest` tag — no versioned pinning; deploy workflow builds and pushes `latest`
- CPU architecture: X86_64 — must use `--platform linux/amd64` when building on Apple Silicon
- Migrations run as separate ECS task before service update in deploy workflow
- CloudFront managed policies referenced via `data` sources, not hardcoded UUIDs
- WAF log group names must start with `aws-waf-logs-` (AWS requirement)
- RDS: force_ssl enabled, Performance Insights on, `pg_stat_statements` preloaded
- S3 lifecycle rules: files bucket (IA 90d, Glacier 365d), SPA (noncurrent 7d), logs buckets (expire 90d)
- `infra/ROLLOUT.md` — cloud environment rollout runbook (state backend, Bedrock enablement, domain config)
- `infra/REVIEW.md` — summary of infrastructure review changes (25 commits, 3 phases)
- Environment values: `poc`, `dev`, `staging`, `prod` — deletion protection and final snapshots are prod-only
