# Lauter — Cloud Environment Rollout Runbook

Step-by-step guide to provision the Lauter AWS environment from scratch.

**Estimated wall-clock time:** ~45 minutes (excluding DNS propagation).
**Estimated monthly cost:** ~$50–85/month for POC (see [Cost Estimate](#cost-estimate)).


## Prerequisites

Before starting, ensure you have:

| Requirement | How to verify |
|---|---|
| AWS CLI v2 installed | `aws --version` |
| Terraform = 1.14.5 installed | `terraform --version` |
| Python 3.12+ installed (for Lambda layer build) | `python3 --version` |
| Docker installed | `docker --version` |
| Bun installed (for SPA build) | `bun --version` |
| AWS credentials configured | `aws sts get-caller-identity` |
| IAM permissions: create VPC, RDS, ECS, S3, CloudFront, Cognito, IAM roles, ACM, WAF, Secrets Manager | Check with your account admin |
| A domain you control (e.g. `lauter.provectus.com`) | Access to DNS management console |
| Google OAuth 2.0 credentials created ([instructions](#step-1-create-google-oauth-credentials)) | Client ID + Client Secret in hand |
| Amazon Bedrock Claude model access enabled in `us-east-1` ([instructions](#step-2-enable-bedrock-model-access)) | Console shows "Access granted" |

Store your AWS account ID — you'll use it throughout:

```bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $ACCOUNT_ID
```


## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. Configure OAuth consent screen if prompted:
   - User Type: **Internal** (corporate Workspace)
   - App name: `Lauter Recruitment Tool`
   - Authorized domains: your domain (e.g. `provectus.com`)
4. Create the client:
   - Application type: **Web application**
   - Name: `Lauter OAuth Client`
   - Authorized redirect URI: `https://lauter-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse`
5. Save the **Client ID** and **Client Secret** for Step 6


## Step 2: Enable Bedrock Model Access

1. Open [Bedrock Model Access](https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess)
2. Click **Manage model access**
3. Enable: Anthropic Claude Sonnet 4.6, Claude Haiku 4.5
4. Accept terms, click **Request model access**
5. Wait for "Access granted" (typically instant)

This is optional for initial deployment — set `enable_bedrock = false` in tfvars to skip.


## Step 3: Create Terraform State Backend

The S3 bucket and DynamoDB table must exist before `terraform init`.

```bash
# S3 bucket for state storage
aws s3api create-bucket \
  --bucket lauter-terraform-state-${ACCOUNT_ID} \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket lauter-terraform-state-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket lauter-terraform-state-${ACCOUNT_ID} \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Block public access
aws s3api put-public-access-block \
  --bucket lauter-terraform-state-${ACCOUNT_ID} \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# DynamoDB table for state locking
aws dynamodb create-table \
  --table-name lauter-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Verify:

```bash
aws s3api head-bucket --bucket lauter-terraform-state-${ACCOUNT_ID}
aws dynamodb describe-table --table-name lauter-terraform-locks --query 'Table.TableStatus'
# Expected: "ACTIVE"
```


## Step 4: Create JWT Secret in Secrets Manager

The backend needs a JWT signing key stored in Secrets Manager. Terraform references its ARN but does not create it.

```bash
JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')

JWT_SECRET_ARN=$(aws secretsmanager create-secret \
  --name lauter/jwt-secret-key \
  --description "JWT signing key for Lauter backend" \
  --secret-string "${JWT_SECRET}" \
  --region us-east-1 \
  --query ARN --output text)

echo "jwt_secret_key_arn = \"${JWT_SECRET_ARN}\""
```

Save the output ARN — you need it for `terraform.tfvars` in Step 6.


## Step 5: Update Backend Config in versions.tf

Replace the `ACCOUNT_ID` placeholder on line 17 of `infra/versions.tf`:

```bash
cd infra
sed -i '' "s/ACCOUNT_ID/${ACCOUNT_ID}/" versions.tf
```

Verify the file now reads:

```hcl
bucket = "lauter-terraform-state-123456789012"  # your actual account ID
```


## Step 6: Prepare terraform.tfvars

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with actual values:

| Variable | Example | Notes |
|---|---|---|
| `region` | `"us-east-1"` | Do not change unless relocating all resources |
| `project_name` | `"lauter"` | Used in all resource name prefixes |
| `environment` | `"poc"` | One of: `poc`, `dev`, `staging`, `prod` |
| `owner` | `"recruitment-team"` | Team/person tag on all resources |
| `domain` | `"lauter.provectus.com"` | Must match your DNS zone |
| `github_repo` | `"provectus/recruitment-framework"` | Format: `org/repo` |
| `google_client_id` | `"123...apps.googleusercontent.com"` | From Step 1 |
| `google_client_secret` | `"GOCSPX-..."` | From Step 1 |
| `jwt_secret_key_arn` | `"arn:aws:secretsmanager:us-east-1:..."` | From Step 4 |
| `enable_bedrock` | `false` | Set `true` after Step 2 when ready |
| `alert_email` | `"team@provectus.com"` | CloudWatch alarm notifications (optional) |
| `bedrock_model_id_heavy` | `"us.anthropic.claude-sonnet-4-6-v1:0"` | Heavy eval tasks (default works) |
| `bedrock_model_id_light` | `"us.anthropic.claude-haiku-4-5-20251001-v1:0"` | Light eval tasks (default works) |

Sensitive variables can also be passed via env vars:

```bash
export TF_VAR_google_client_secret="GOCSPX-..."
export TF_VAR_jwt_secret_key_arn="arn:aws:secretsmanager:..."
```

**Never commit `terraform.tfvars`** — it is already in `.gitignore`.


## Step 7: Terraform Init / Plan / Apply

### Init

```bash
cd infra
terraform init
```

Expected: `Terraform has been successfully initialized!`

If you see `Error configuring S3 Backend`, double-check the bucket name in `versions.tf` matches what you created in Step 3.

### Plan

```bash
terraform plan -out=tfplan
```

Expected: **~120 resources** to add, 0 to change, 0 to destroy. Review the plan for:
- VPC + 2 public subnets + 2 private subnets + NAT Gateway
- RDS PostgreSQL instance (`db.t4g.micro`)
- 3 S3 buckets (SPA + files + CloudFront logs) + ALB access logs bucket
- ECS cluster + Fargate service + ALB
- CloudFront distribution
- Cognito User Pool + Google IdP
- ACM certificate
- WAF WebACLs (2: one for ALB, one for CloudFront)
- IAM roles (execution, task, GitHub Actions) + OIDC provider + ECR repository
- Evaluation pipeline: EventBridge custom bus + Step Functions state machine + 5 Lambda functions + shared Lambda layer
- CloudWatch log group + alarms + SNS topic

### Apply

```bash
terraform apply tfplan
```

**Duration:** ~10-15 minutes. The slowest resources are:
- NAT Gateway (~2 min)
- RDS instance (~5-8 min)
- CloudFront distribution (~3-5 min)

The ACM certificate will show as created but **not yet validated** — that happens in Step 8.

### Save outputs

```bash
terraform output > /tmp/lauter-outputs.txt
```


## Step 8: Post-Apply DNS Setup

### ACM Certificate Validation

Terraform outputs the CNAME records needed to validate the SSL certificate:

```bash
terraform output domain_validation_records
```

This returns records like:

```
domain_name           = "lauter.provectus.com"
resource_record_name  = "_abc123.lauter.provectus.com."
resource_record_type  = "CNAME"
resource_record_value = "_xyz789.acm-validations.aws."
```

Create **all** returned CNAME records in your DNS zone. There will be one per domain (base domain + wildcard = typically 1-2 records, often deduplicated to 1).

**Wait for validation** — can take up to 30 minutes. Monitor:

```bash
aws acm describe-certificate \
  --certificate-arn $(terraform output -raw certificate_arn) \
  --query 'Certificate.Status'
# Wait until: "ISSUED"
```

### Domain CNAME Record

Both the SPA and API are served through CloudFront (API calls are routed via `/api/*` path to the ALB). Only one DNS record is needed:

```bash
echo "Create CNAME: YOUR_DOMAIN → $(terraform output -raw cloudfront_distribution_domain)"
```

| Record | Type | Value |
|---|---|---|
| `lauter.provectus.com` | CNAME | CloudFront domain from output |

**Note:** If using Route53 for DNS, use an A-alias record instead of CNAME (avoids CNAME-at-apex limitation). No separate `api.` subdomain is needed — CloudFront routes `/api/*` requests to the ALB origin automatically.

Wait for DNS propagation before proceeding (~5-15 minutes):

```bash
dig lauter.provectus.com +short
```


## Step 9: First Deployment

### 9a. Push Initial Docker Image to ECR

```bash
ECR_URL=$(cd infra && terraform output -raw ecr_repository_url)

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ECR_URL%%/*}

# Build the backend image
cd app/backend
docker build --platform linux/amd64 --target prod -t lauter-backend .

# Tag and push
docker tag lauter-backend:latest ${ECR_URL}:latest
docker push ${ECR_URL}:latest
```

### 9b. Run Database Migrations

The ECS service won't start healthy until the database is migrated. Run Alembic via ECS run-task:

```bash
cd infra

CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
SUBNET_ID=$(terraform output -json private_subnet_ids | jq -r '.[0]')
SG_ID=$(terraform output -raw ecs_security_group_id)

# Get the current task definition from the service
TASK_DEF=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services lauter-backend \
  --query 'services[0].taskDefinition' \
  --output text)

# Run migration
TASK_ARN=$(aws ecs run-task \
  --cluster ${CLUSTER_NAME} \
  --task-definition ${TASK_DEF} \
  --launch-type FARGATE \
  --network-configuration \
    "awsvpcConfiguration={subnets=[${SUBNET_ID}],securityGroups=[${SG_ID}],assignPublicIp=DISABLED}" \
  --overrides \
    '{"containerOverrides":[{"name":"lauter-backend","command":["uv","run","alembic","upgrade","head"]}]}' \
  --query 'tasks[0].taskArn' --output text)

echo "Migration task: ${TASK_ARN}"

# Wait for completion
aws ecs wait tasks-stopped --cluster ${CLUSTER_NAME} --tasks ${TASK_ARN}

# Check exit code
aws ecs describe-tasks \
  --cluster ${CLUSTER_NAME} --tasks ${TASK_ARN} \
  --query 'tasks[0].containers[0].exitCode' --output text
# Expected: 0
```

If the migration fails, check CloudWatch logs:

```bash
aws logs tail /ecs/lauter-backend --since 10m
```

### 9c. Force ECS Service Redeployment

After pushing the image and running migrations, force the service to pick up the new image:

```bash
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service lauter-backend \
  --force-new-deployment

aws ecs wait services-stable \
  --cluster ${CLUSTER_NAME} \
  --services lauter-backend
```

### 9d. Upload Frontend SPA to S3

```bash
cd app/frontend
bun install
bun run build

SPA_BUCKET=$(cd ../../infra && terraform output -raw spa_bucket_id)
CF_DIST_ID=$(cd ../../infra && terraform output -raw cloudfront_distribution_id)

# Sync hashed assets with long cache
aws s3 sync dist/ s3://${SPA_BUCKET}/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html with no-cache
aws s3 cp dist/index.html s3://${SPA_BUCKET}/index.html \
  --cache-control "public, max-age=0, must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id ${CF_DIST_ID} \
  --paths "/*"
```


## Step 10: Configure GitHub Actions Secrets

Go to **GitHub → Repository → Settings → Secrets and variables → Actions** and add:

| Secret name | Value | Used by |
|---|---|---|
| `AWS_ACCOUNT_ID` | Your AWS account ID | All deploy workflows (OIDC role ARN construction) |
| `CLOUDFRONT_DISTRIBUTION_ID` | `terraform output -raw cloudfront_distribution_id` | `deploy-frontend.yml` |

**No static AWS keys needed.** All deploy workflows (backend, frontend, lambdas) use OIDC (`role-to-assume`) with the `lauter-github-actions-role` created by Terraform.

Verify the OIDC role ARN:

```bash
terraform output -raw github_actions_role_arn
# Expected: arn:aws:iam::<ACCOUNT_ID>:role/lauter-github-actions-role
```


## Step 11: Smoke Test Checklist

Run these checks after the first deployment:

```bash
DOMAIN="lauter.provectus.com"  # replace with your domain
```

- [ ] **API health:**
  ```bash
  curl -s https://${DOMAIN}/api/health | jq .
  # Expected: {"status":"ok"}
  ```

- [ ] **SPA loads:**
  ```bash
  curl -s -o /dev/null -w "%{http_code}" https://${DOMAIN}
  # Expected: 200
  ```

- [ ] **HTTPS redirect:**
  ```bash
  curl -s -o /dev/null -w "%{http_code}" http://${DOMAIN}
  # Expected: 301 or 302
  ```

- [ ] **Google OAuth login:** Open `https://${DOMAIN}` in browser → click Login → Google OAuth flow completes → redirected back to app

- [ ] **CloudWatch logs flowing:**
  ```bash
  aws logs tail /ecs/lauter-backend --since 5m --format short
  ```

- [ ] **No ECS task failures:**
  ```bash
  aws ecs describe-services \
    --cluster lauter-cluster --services lauter-backend \
    --query 'services[0].{running:runningCount,desired:desiredCount,deployments:deployments[*].rolloutState}'
  # Expected: running=1, desired=1, rolloutState=COMPLETED
  ```

- [ ] **SNS alarm subscription confirmed** (if `alert_email` was set): Check the email and confirm the subscription


## Architecture Summary

### Resource Map

```
Internet
  │
  └─► CloudFront (domain)
        ├── WAF WebACL
        ├── /api/* ──► ALB ──► ECS Fargate (lauter-backend, 0.25 vCPU / 0.5 GB)
        │                └── WAF WebACL   ├── RDS PostgreSQL 16 (db.t4g.micro, 20 GB)
        │                                 ├── S3 bucket (lauter-files-*)
        │                                 ├── Cognito (Google OAuth)
        │                                 ├── Secrets Manager (DB password, JWT key, Cognito secret)
        │                                 └── EventBridge ──► Step Functions ──► 5 Lambdas
        │                                                                         ├── Bedrock (Claude Sonnet/Haiku)
        │                                                                         ├── RDS (direct write)
        │                                                                         └── S3 (file read)
        └── /* (default) ──► S3 bucket (lauter-spa-*)
```

### Module Dependency Diagram

```
networking ──────────┬──► ecs ◄── iam ◄── s3
                     │     │               ▲
                     ├──► rds          cloudfront ◄── acm
                     │     │              ▲  ▲
                     ├──► evaluation_pipeline  waf  └── ecs (ALB origin)
                     │     ├── rds (address, secret)
                     │     └── s3 (files bucket)
                     │
                     └──► (security groups shared across ecs, rds, lambdas)

cognito ──► ecs (SSM params, secrets)
iam ◄── evaluation_pipeline (event bus ARN)
ecs ◄── evaluation_pipeline (event bus name)
monitoring ◄── ecs (ALB metrics), rds (DB metrics)
```

### Cost Estimate (POC)

| Resource | Estimated monthly cost |
|---|---|
| NAT Gateway (1 AZ) | ~$32 |
| RDS db.t4g.micro (Single-AZ) | ~$12 |
| ALB | ~$16 + data |
| ECS Fargate (0.25 vCPU / 0.5 GB) | ~$8 |
| CloudFront | ~$1 (low traffic) |
| S3 (all buckets) | < $1 |
| Secrets Manager (3 secrets) | < $2 |
| Lambda (5 functions, low volume) | < $1 |
| Step Functions (standard, low volume) | < $1 |
| CloudWatch | < $2 |
| WAF (2 WebACLs) | ~$10 |
| **Total** | **~$50–85/month** |

The NAT Gateway is the largest cost driver. For a tighter budget, consider a NAT instance or VPC endpoints instead.


## Troubleshooting

### `terraform init` fails with S3 backend error

**Cause:** State bucket doesn't exist or name doesn't match `versions.tf`.

```bash
# Verify bucket exists
aws s3api head-bucket --bucket lauter-terraform-state-${ACCOUNT_ID}

# Verify versions.tf has the correct bucket name
grep bucket infra/versions.tf
```

### `terraform apply` hangs on ACM certificate

**Cause:** The ACM module may include a `aws_acm_certificate_validation` resource that waits for DNS validation.

**Fix:** Create the DNS validation CNAME records (from `terraform output domain_validation_records`) in a separate terminal while apply is running. Alternatively, apply with `-target` to skip the validation initially.

### ECS service keeps restarting (tasks fail health check)

**Cause:** Usually the container can't reach RDS or the image doesn't exist in ECR.

```bash
# Check task stopped reason
aws ecs describe-tasks \
  --cluster lauter-cluster \
  --tasks $(aws ecs list-tasks --cluster lauter-cluster --service lauter-backend --query 'taskArns[0]' --output text) \
  --query 'tasks[0].{status:lastStatus,reason:stoppedReason,container:containers[0].reason}'

# Check application logs
aws logs tail /ecs/lauter-backend --since 15m
```

Common fixes:
- **No image in ECR:** Complete Step 9a first
- **DB connection error:** Verify RDS is in `available` state and security group allows ECS → RDS on port 5432
- **Secrets Manager error:** Verify the JWT secret ARN in tfvars matches the one created in Step 4

### CloudFront returns 403

**Cause:** S3 bucket is empty or OAC policy isn't applied.

```bash
# Check if SPA files exist
aws s3 ls s3://$(cd infra && terraform output -raw spa_bucket_id)/
```

If empty, complete Step 9d. If files exist, verify the CloudFront OAC is configured (check CloudFront → Origins in AWS Console).

### GitHub Actions deploy fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity"

**Cause:** OIDC trust policy doesn't match the GitHub repo or the `AWS_ACCOUNT_ID` secret is wrong.

```bash
# Verify the trust policy
aws iam get-role --role-name lauter-github-actions-role \
  --query 'Role.AssumeRolePolicyDocument'
```

Check that:
1. The `AWS_ACCOUNT_ID` GitHub secret matches your actual account ID
2. The `github_repo` variable in tfvars matches your actual `org/repo`
3. The deploy workflow is running on the `main` branch (OIDC trust is branch-scoped)

### Terraform state lock stuck

If a previous `terraform apply` was interrupted:

```bash
# Check for lock
aws dynamodb get-item \
  --table-name lauter-terraform-locks \
  --key '{"LockID":{"S":"lauter-terraform-state-'${ACCOUNT_ID}'/lauter/terraform.tfstate"}}'

# Force unlock (only if you're sure no other apply is running)
terraform force-unlock <LOCK_ID>
```

### Google OAuth callback returns error

**Cause:** Redirect URI mismatch between Google Console and Cognito.

Verify the redirect URI in Google Cloud Console matches:
```
https://lauter-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse
```

The Cognito hosted UI domain prefix (`lauter-auth`) is set by Terraform. Check:
```bash
aws cognito-idp describe-user-pool \
  --user-pool-id $(aws ssm get-parameter --name /lauter/poc/cognito/user-pool-id --query 'Parameter.Value' --output text) \
  --query 'UserPool.Domain'
```
