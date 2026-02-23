# Infrastructure Review — Summary of Changes

**Branch:** `feature/infra-ci-setup`
**Date:** February 2026
**Scope:** 25 commits across 3 phases — provider modernization, security hardening, monitoring

## Version Targets

| Component | Before | After |
|---|---|---|
| Terraform CLI | `>= 1.5` (CI: `~1.5`) | `~> 1.14.5` (CI: `1.14.5`) |
| AWS provider | `~> 5.0` (lock: 5.100.0) | `~> 6.33` (lock: 6.33.0) |
| TLS provider | 4.2.1 (undeclared) | **Removed** |

---

## Phase 1 — Provider Upgrades & Config Fixes

1. **Pin Terraform 1.14.5 + AWS provider 6.33.0** — updated `required_version`, provider constraint, CI exact pin. Fixed 3 deprecated `data.aws_region.current.name` → `.region` references (cognito, ecs modules).

2. **Modernize OIDC thumbprint** — replaced dynamic TLS certificate lookup with static thumbprint (AWS manages GitHub OIDC server-side since 2023). Removed TLS provider dependency entirely.

3. **Hardcoded "lauter" → variables** — added root variables `db_name`, `db_username`, `allowed_email_domain` and wired through to rds/ecs modules. RDS `username` now reads from `var.db_username`.

4. **Cognito SSM paths** — changed `/lauter/cognito/*` → `/${var.project_name}/cognito/*` in SSM parameter names and descriptions.

5. **Tag consistency** — removed per-resource `ManagedBy = "terraform"` that conflicted with `default_tags` (`ManagedBy = "Terraform"`). Added `environment` variable to cognito module.

6. **Dynamic availability zones** — added `data.aws_availability_zones` lookup. AZ variable defaults to `null` (auto-discovered) instead of hardcoded `us-east-1a/1b`.

7. **Configurable ECS sizing** — added `task_cpu`, `task_memory`, `image_tag` variables to ecs module (defaults: 256/512/latest).

8. **CloudFront managed policy data sources** — replaced 3 hardcoded UUIDs with `data.aws_cloudfront_cache_policy` / `data.aws_cloudfront_origin_request_policy` lookups.

9. **OIDC branch pattern** — added `github_actions_branch_pattern` variable (default: `ref:refs/heads/main`). Can be widened to `*` for PR-level CI.

---

## Phase 2 — Security Hardening

1. **RDS force_ssl** — added `rds.force_ssl = 1` parameter. Removed duplicate `ecs_task_secrets` IAM policy (execution role already handles secret injection).

2. **Cognito deletion protection** — added `deletion_protection = "ACTIVE"` to user pool.

3. **VPC Flow Logs** — added CloudWatch log group (`/vpc/${project}-flow-logs`, 14-day retention), IAM role, and `aws_flow_log` resource capturing all traffic.

4. **WAF logging** — added CloudWatch log groups (`aws-waf-logs-*`, 30-day retention) and logging configurations for both CloudFront and ALB WAFs.

5. **S3 TLS enforcement** — added bucket policy on files bucket denying `s3:*` when `aws:SecureTransport = false`.

6. **WAF rule groups** — added `AWSManagedRulesAmazonIpReputationList` (both WAFs) and `AWSManagedRulesSQLiRuleSet` (ALB WAF only).

7. **ECS Exec permissions** — added conditional SSM policy (`ssmmessages:*`) on task role, gated by `enable_ecs_exec` variable. Enabled for non-prod environments.

8. **GitHub Actions role tightening** — removed `ecs:StopTask` from CI/CD role (destructive permission unnecessary for deployments).

9. **Frontend deploy timeouts** — added `timeout-minutes: 15` (test) and `10` (deploy) to `deploy-frontend.yml`.

10. **ALB logs safety** — changed `force_destroy = false` on ALB logs bucket (was `true`).

---

## Phase 3 — Monitoring & Observability

1. **Expanded CloudWatch alarms** — added `ok_actions` (recovery notifications) to existing alarms. Added 5 new alarms: ALB 5xx errors, ALB p99 response time, ECS CPU utilization, RDS free storage, RDS connection count.

2. **RDS Performance Insights** — enabled Performance Insights (7-day free tier), CloudWatch log exports (postgresql, upgrade), and storage autoscaling (`max_allocated_storage`).

3. **RDS parameter tuning** — added `log_min_duration_statement = 1000` (log queries >1s), `shared_preload_libraries = pg_stat_statements`, `pg_stat_statements.track = all`.

4. **S3 lifecycle rules** — files bucket: IA at 90 days, Glacier at 365 days, noncurrent expiry at 90 days. SPA bucket: noncurrent expiry at 7 days (old deploys).

5. **CloudFront access logging** — created dedicated logs bucket with `BucketOwnerPreferred` ownership and 90-day expiry. Added `logging_config` to CloudFront distribution.

6. **Tag deduplication** — removed per-resource `Project` and `Environment` tags from 5 modules (29 resources). Root `default_tags` already propagates these.

---

## Deferred Items

| # | Item | Reason |
|---|---|---|
| 1 | ACM certificate validation | Requires Route53 zone decision |
| 2 | ALB direct access restriction | Architecture change needed (CF prefix list or origin-verify header) |
| 3 | ECR IMMUTABLE tags | Requires CI pipeline change (SHA-only tags) |
| 4 | Cognito MFA | UX decision needed (TOTP vs SMS, optional vs required) |
| 5 | ECS egress SG tightening | Needs VPC endpoints first |
| 6 | VPC Endpoints | ~$7/endpoint/month; architecture decision |
| 7 | Multi-AZ NAT Gateway | ~$32/month extra; acceptable for POC |
| 8 | Multi-environment support | Architecture decision (workspaces vs directories) |
| 9 | SSE-KMS on S3 files bucket | Adds CMK cost; needs compliance discussion |
| 10 | n8n networking | Zero infra exists; needs VPN/Transit Gateway decisions |
| 11 | ECS health check (curl) | Dockerfile change; ALB health check is authoritative |
| 12 | ROLLOUT.md backend-config | Docs issue; should use `-backend-config` partial config |
| 13 | `required_providers` in modules | Best practice but not blocking |
| 14 | JWT secret rotation | Needs rotation Lambda + session invalidation |
| 15 | Cost controls (AWS Budgets) | Ops concern, separate from code quality |
| 16 | CSP `connect-src` tightening | Need to enumerate exact Cognito domain |
| 17 | TFLint AWS plugin upgrade | May need newer version for provider 6.x schemas |
