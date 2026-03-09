# Tasks: Infrastructure — AWS Environment & CI/CD

---

## Slice 0: Terraform project foundation + networking

Terraform project initialized with remote state backend config and the networking module. After this slice, `terraform init` + `terraform validate` pass and `terraform plan` shows VPC resources.

- [x] Create `infra/` directory structure: `main.tf` (AWS provider for us-east-1, S3 backend config), `variables.tf` (region, project name, domain, environment), `outputs.tf` (placeholder) **[Agent: terraform-infrastructure]**
- [x] Create `infra/README.md` documenting manual state backend setup: create S3 bucket `tap-terraform-state-<account-id>` (versioning enabled) and DynamoDB table `tap-terraform-locks` (partition key `LockID`) **[Agent: terraform-infrastructure]**
- [x] Create `infra/modules/networking/`: VPC (`10.0.0.0/16`), public subnets (2 AZs), private subnets (2 AZs), Internet Gateway, single NAT Gateway, route tables, security groups (`alb-sg`, `ecs-sg`, `rds-sg`) per tech spec §2.2 **[Agent: terraform-infrastructure]**
- [x] Wire networking module into `main.tf`, expose VPC ID, subnet IDs, and security group IDs as outputs **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform init` succeeds (with `-backend=false` or local backend for validation), `terraform validate` passes, `terraform fmt --check` passes **[Agent: terraform-infrastructure]**

---

## Slice 1: Data + storage (RDS + S3)

Database and storage buckets defined. Plan shows RDS instance and S3 buckets.

- [x] Create `infra/modules/rds/`: PostgreSQL 16 on `db.t4g.micro`, 20 GB gp3, private subnets, `manage_master_user_password = true` (Secrets Manager), automated backups (7-day retention), encryption at rest per tech spec §2.4 **[Agent: terraform-infrastructure]**
- [x] Create `infra/modules/s3/`: SPA bucket (`tap-spa-*`) with block public access + CloudFront OAC policy, files bucket (`tap-files-*`) with block public access, both with versioning + SSE-S3 per tech spec §2.5 **[Agent: terraform-infrastructure]**
- [x] Wire RDS and S3 modules into `main.tf`, pass networking outputs (private subnet IDs, `rds-sg`), expose RDS endpoint and S3 bucket names/ARNs as outputs **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows RDS instance + 2 S3 buckets **[Agent: terraform-infrastructure]**

---

## Slice 2: IAM + ECR

All IAM roles and the container registry. Includes Bedrock invoke policy on task role and GitHub Actions OIDC provider.

- [x] Create `infra/modules/iam/`: `tap-ecs-execution-role` (ECR pull, Secrets Manager read, CloudWatch Logs write), `tap-ecs-task-role` (S3 read/write on files bucket, `bedrock:InvokeModel` scoped to Claude model ARN, Secrets Manager read), `tap-github-actions-role` (ECR push, ECS update, S3 sync on SPA bucket, CloudFront invalidation), GitHub OIDC provider per tech spec §2.7 **[Agent: terraform-infrastructure]**
- [x] Add ECR repository `tap-backend` to the ECS module or as a standalone resource in `main.tf` **[Agent: terraform-infrastructure]**
- [x] Wire IAM module into `main.tf`, pass GitHub repo name as variable for OIDC trust policy, expose role ARNs as outputs **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows IAM roles + OIDC provider + ECR repo **[Agent: terraform-infrastructure]**

---

## Slice 3: ACM certificate

SSL certificate for custom domain. Output includes DNS validation records for the user to create manually.

- [x] Create `infra/modules/acm/`: wildcard certificate (`*.<domain>` + `<domain>`), DNS validation, output validation CNAME records per tech spec §2.6 **[Agent: terraform-infrastructure]**
- [x] Wire ACM module into `main.tf`, pass domain variable **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows ACM certificate resource **[Agent: terraform-infrastructure]**

---

## Slice 4: ECS + ALB (Backend compute)

Backend compute stack. ALB with HTTPS listener using ACM cert, ECS Fargate service running the backend container.

- [x] Create `infra/modules/ecs/`: ECS cluster (`tap-cluster`), Fargate task definition (0.25 vCPU / 0.5 GB, port 8000, health check `/health`), ECS service (desired count 1, circuit breaker enabled, private subnets), ALB (internet-facing, public subnets, HTTPS listener with ACM cert for `api.<domain>`, HTTP→HTTPS redirect), target group (port 8000, health check `/health`, 30s deregistration delay) per tech spec §2.3 **[Agent: terraform-infrastructure]**
- [x] Configure container environment variables: `DATABASE_URL` and `JWT_SECRET_KEY` from Secrets Manager, `COGNITO_*` from SSM Parameter Store, `CORS_ORIGINS`, `COOKIE_DOMAIN`, `COOKIE_SECURE` as plain values per tech spec §2.3 **[Agent: terraform-infrastructure]**
- [x] Wire ECS module into `main.tf`, pass networking outputs, IAM role ARNs, ECR repo URL, RDS secret ARN, ACM cert ARN. Expose ALB DNS name as output. **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows ECS cluster + service + ALB + target group **[Agent: terraform-infrastructure]**

---

## Slice 5: CloudFront (Frontend CDN)

CloudFront distribution serving the React SPA from S3 with SPA fallback routing.

- [x] Create `infra/modules/cloudfront/`: distribution with S3 origin via OAC, default root object `index.html`, custom error responses (403/404 → `/index.html` with 200), `CachingOptimized` cache policy, alternate domain `<domain>`, ACM cert, `PriceClass_100` per tech spec §2.6 **[Agent: terraform-infrastructure]**
- [x] Wire CloudFront module into `main.tf`, pass SPA bucket details + ACM cert ARN. Expose CloudFront distribution domain and ID as outputs. **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows CloudFront distribution + OAC **[Agent: terraform-infrastructure]**

---

## Slice 6: Cognito (Auth infrastructure)

Cognito User Pool with Google federated identity provider, app client, and hosted UI domain.

- [x] Create `infra/modules/cognito/`: User Pool (`tap-users`, email as username), Google Identity Provider (client ID + secret from TF variables), App Client (`tap-web-client`, authorization code grant, scopes `openid email profile`, callback URL `https://api.<domain>/auth/callback`, sign-out URL `https://<domain>/login`), hosted UI domain per tech spec §2.8 **[Agent: terraform-infrastructure]**
- [x] Store Cognito outputs in SSM/Secrets Manager: `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID` as SSM parameters, `COGNITO_CLIENT_SECRET` in Secrets Manager, `COGNITO_DOMAIN` as SSM parameter **[Agent: terraform-infrastructure]**
- [x] Wire Cognito module into `main.tf`, pass domain variable + Google OAuth credentials as sensitive variables. Ensure ECS task definition references the SSM/Secrets Manager values created here. **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows Cognito User Pool + IdP + app client + domain + SSM params **[Agent: terraform-infrastructure]**

---

## Slice 7: Monitoring

CloudWatch log groups, ALB access logs, alarms, and SNS alerting topic.

- [x] Create `infra/modules/monitoring/`: CloudWatch log group `/ecs/tap-backend` (30-day retention), ALB access logs bucket, alarms (ECS unhealthy: `UnHealthyHostCount > 0` for 5 min; RDS CPU: `CPUUtilization > 80%` for 10 min), SNS topic `tap-alerts` per tech spec §2.10 **[Agent: terraform-infrastructure]**
- [x] Wire monitoring module into `main.tf`, pass ALB ARN, ECS service name, RDS instance ID. **[Agent: terraform-infrastructure]**
- [x] **Verify:** `terraform validate` passes, `terraform plan` shows log group + alarms + SNS topic. Full plan across all modules produces a clean diff with no errors. **[Agent: terraform-infrastructure]**

---

## Slice 8: First deployment (manual prerequisites + apply + smoke test)

Manual steps that cannot be automated by a subagent: state backend creation, DNS setup, Google OAuth credentials, `terraform apply`, initial image push, database migration, SPA upload.

- [x] Document all manual prerequisites in `infra/README.md`: (1) create TF state backend (S3 + DynamoDB), (2) create Google OAuth app in Google Cloud Console, (3) choose domain and create DNS zone, (4) enable Bedrock Claude model access in us-east-1 console **[Agent: terraform-infrastructure]**
- [x] Create `infra/terraform.tfvars.example` listing all required variables with placeholder values (region, domain, project name, Google OAuth client ID/secret, GitHub repo) **[Agent: terraform-infrastructure]**
- [ ] **Verify (manual):** User runs `terraform apply`, creates DNS validation records for ACM, pushes initial Docker image to ECR (`docker build --target prod -t tap-backend . && docker push`), runs Alembic migration via ECS run-task, uploads SPA build to S3. Smoke test: `curl https://api.<domain>/health` → 200, `https://<domain>` → SPA loads, Google OAuth login flow works end-to-end.

---

## Slice 9: CI/CD — Backend pipeline

GitHub Actions workflow that builds, tests, and deploys the FastAPI backend on push to main.

- [x] Create `.github/workflows/deploy-backend.yml`: trigger on push to `main` (paths `app/backend/**`), `test` job (checkout, setup Python + uv, `ruff check`, `ruff format --check`, `pytest`), `deploy` job (OIDC AWS auth with `tap-github-actions-role`, build Docker image with `prod` target, push to ECR, update ECS service, wait for stability) per tech spec §2.11 **[Agent: general-purpose]**
- [x] Add PR trigger (test job only, no deploy) so lint/test status shows on PRs **[Agent: general-purpose]**
- [ ] **Verify:** Push a change to `app/backend/` on `main` → workflow triggers, test job passes, deploy job pushes image to ECR and updates ECS service. On a PR, only the test job runs.

---

## Slice 10: CI/CD — Frontend pipeline

GitHub Actions workflow that builds, tests, and deploys the React SPA on push to main.

- [x] Create `.github/workflows/deploy-frontend.yml`: trigger on push to `main` (paths `app/frontend/**`), `test` job (checkout, setup Bun, `bun run lint`, `bun run build`), `deploy` job (OIDC AWS auth, sync `dist/` to SPA S3 bucket, invalidate CloudFront cache) per tech spec §2.11 **[Agent: general-purpose]**
- [x] Add PR trigger (test job only, no deploy) so lint/build status shows on PRs **[Agent: general-purpose]**
- [ ] **Verify:** Push a change to `app/frontend/` on `main` → workflow triggers, test job passes, deploy job syncs to S3 and invalidates CloudFront. On a PR, only the test job runs.

---

## Recommendations

| Task/Slice | Issue | Recommendation |
|------------|-------|----------------|
| Slice 8 (First deployment) | Requires manual AWS credentials, DNS setup, Google OAuth app | Cannot be automated — document steps clearly in `infra/README.md` |
| Slice 8 (Bedrock) | Model access enablement is a console-only action | Manual one-time step, not Terraform-managed |
| Slices 9-10 verification | Requires pushing to GitHub + valid OIDC trust | Test after `terraform apply` has created the OIDC provider and IAM role |
| All Terraform slices | `terraform plan` requires AWS credentials | Agent can run `terraform validate` + `terraform fmt`; `terraform plan` requires credentials to be configured |
