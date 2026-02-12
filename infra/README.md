# Terraform Infrastructure

## Overview

This directory contains Terraform infrastructure-as-code for **Tap** — an internal recruitment workflow automation tool for Provectus. The infrastructure provisions all AWS resources required to run the application in the `us-east-1` region, including VPC networking, RDS PostgreSQL database, S3 storage, CloudFront CDN, and authentication services.

Target environment: Single POC environment in AWS.

## Prerequisites

Before working with this infrastructure, ensure you have:
- AWS CLI configured with credentials for the target AWS account
- Terraform >= 1.5 installed
- Access permissions to create IAM roles, VPCs, RDS instances, and other AWS resources
- Your AWS account ID (retrieve with `aws sts get-caller-identity`)

## Manual Pre-Deployment Steps

Complete ALL of the following manual steps before running `terraform apply`. These are one-time setup operations that cannot be automated via Terraform.

### 1. Manual State Backend Setup

**IMPORTANT:** The Terraform state backend (S3 bucket and DynamoDB table) must be created manually before running `terraform init`. This is a one-time setup per AWS account.

### Create S3 Bucket for State Storage

Replace `<ACCOUNT_ID>` with your actual AWS account ID in all commands below:

```bash
aws s3api create-bucket \
  --bucket tap-terraform-state-<ACCOUNT_ID> \
  --region us-east-1
```

Enable versioning to protect against accidental deletions:

```bash
aws s3api put-bucket-versioning \
  --bucket tap-terraform-state-<ACCOUNT_ID> \
  --versioning-configuration Status=Enabled
```

Enable server-side encryption:

```bash
aws s3api put-bucket-encryption \
  --bucket tap-terraform-state-<ACCOUNT_ID> \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

Block public access:

```bash
aws s3api put-public-access-block \
  --bucket tap-terraform-state-<ACCOUNT_ID> \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### Create DynamoDB Table for State Locking

```bash
aws dynamodb create-table \
  --table-name tap-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Update Backend Configuration

After creating the S3 bucket and DynamoDB table, update the `bucket` value in `main.tf` backend configuration with your actual bucket name:

```hcl
terraform {
  backend "s3" {
    bucket         = "tap-terraform-state-<ACCOUNT_ID>"  # Replace <ACCOUNT_ID>
    key            = "tap/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tap-terraform-locks"
    encrypt        = true
  }
}
```

### 2. Create Google OAuth Application

Set up Google OAuth 2.0 credentials for user authentication:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services → Credentials**
3. Click **Create Credentials → OAuth 2.0 Client ID**
4. Configure the OAuth consent screen if prompted:
   - User Type: Internal (for corporate Workspace)
   - App name: "Tap Recruitment Tool"
   - User support email: your-email@provectus.com
   - Authorized domains: your-domain.com
5. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Name: "Tap OAuth Client"
   - Authorized redirect URIs: `https://tap-auth.auth.us-east-1.amazoncognito.com/oauth2/idpresponse`
     (Note: The exact URI will match the pattern `https://{cognito-domain}.auth.{region}.amazoncognito.com/oauth2/idpresponse`)
6. Save the **Client ID** and **Client Secret** — you will need these for `terraform.tfvars`

### 3. Choose Domain and Prepare DNS

Choose a custom domain for the application (e.g., `tap.provectus.com`). You will need to create DNS records after Terraform deployment:

**Required DNS Records (to be created after `terraform apply`):**

1. **ACM Certificate Validation CNAME:**
   - Terraform will output the CNAME records required to validate the SSL certificate
   - Add these records to your DNS zone
   - Wait for validation to complete (can take up to 30 minutes)

2. **API Endpoint:**
   - Record: `api.your-domain.com`
   - Type: CNAME or A-alias
   - Value: ALB DNS name (output by Terraform as `api_endpoint`)

3. **Frontend SPA:**
   - Record: `your-domain.com`
   - Type: CNAME or A-alias
   - Value: CloudFront distribution domain (output by Terraform as `cloudfront_domain_name`)

### 4. Enable Amazon Bedrock Model Access

Enable access to Anthropic Claude models in Amazon Bedrock (us-east-1):

1. Open [AWS Console → Amazon Bedrock → Model access](https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess)
2. Click **Manage model access** or **Edit**
3. Select the following models:
   - Anthropic Claude 3 Sonnet
   - Anthropic Claude 3.5 Sonnet (recommended)
   - Anthropic Claude 3 Haiku
4. Review terms and click **Request model access**
5. Wait for access to be granted (typically instant for standard models)

This is a **one-time manual step** per AWS account — Terraform cannot automate model access requests.

### 5. Create terraform.tfvars Configuration

Copy the example configuration and fill in your actual values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your actual values (see `terraform.tfvars.example` for complete list).

**IMPORTANT:** Never commit `terraform.tfvars` to version control. It is already in `.gitignore`.

## Getting Started

Navigate to the infrastructure directory:

```bash
cd infra
```

Initialize Terraform (downloads providers and configures backend):

```bash
terraform init
```

Validate configuration syntax:

```bash
terraform validate
```

Preview infrastructure changes:

```bash
terraform plan -var="domain=your-domain.com"
```

Apply infrastructure changes:

```bash
terraform apply -var="domain=your-domain.com"
```

Destroy infrastructure (use with caution):

```bash
terraform destroy -var="domain=your-domain.com"
```

## First Deployment Steps

After running `terraform apply` successfully, complete these steps to deploy the application:

### 1. Create DNS Records

Using the Terraform outputs, create the DNS records documented in **Manual Pre-Deployment Steps → Step 3**.

View Terraform outputs:

```bash
terraform output
```

### 2. Push Initial Docker Image to ECR

Terraform creates the ECR repository but does not push images. Build and push the initial backend image:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build the backend Docker image (from repository root)
cd app/backend
docker build --target prod -t tap-backend .

# Tag the image for ECR
docker tag tap-backend:latest ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/tap-backend:latest

# Push to ECR
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/tap-backend:latest
```

### 3. Run Database Migrations

Run Alembic migrations via ECS run-task:

```bash
# Get cluster and task definition ARNs from Terraform output
CLUSTER_ARN=$(terraform output -raw ecs_cluster_arn)
TASK_DEF=$(terraform output -raw ecs_task_definition_arn)
SUBNET_ID=$(terraform output -json private_subnet_ids | jq -r '.[0]')
SECURITY_GROUP=$(terraform output -raw ecs_security_group_id)

# Run migration task
aws ecs run-task \
  --cluster ${CLUSTER_ARN} \
  --task-definition ${TASK_DEF} \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_ID}],securityGroups=[${SECURITY_GROUP}],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"tap-backend","command":["alembic","upgrade","head"]}]}'
```

Monitor the task in ECS Console to confirm migrations complete successfully.

### 4. Upload Frontend SPA to S3

Build and deploy the React SPA:

```bash
# Navigate to frontend directory (from repository root)
cd app/frontend

# Install dependencies and build
bun install
bun run build

# Get S3 bucket name and CloudFront distribution ID
BUCKET_NAME=$(terraform output -raw spa_bucket_name)
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)

# Sync build output to S3
aws s3 sync dist/ s3://${BUCKET_NAME}/ --delete

# Invalidate CloudFront cache to serve new version
aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths "/*"
```

Wait for CloudFront invalidation to complete (typically 1-3 minutes).

### 5. Smoke Test

Verify the deployment:

```bash
# Test API health endpoint
API_URL=$(terraform output -raw api_endpoint)
curl https://${API_URL}/health

# Expected response: {"status":"healthy"}
```

Open the frontend URL in a browser:

```bash
FRONTEND_URL=$(terraform output -raw cloudfront_url)
echo "Frontend: https://${FRONTEND_URL}"
```

Test Google OAuth login flow and verify the application is functional.

## Module Structure

The infrastructure is organized into reusable modules:

```
infra/
  main.tf          — Root module, backend config, provider, module composition
  variables.tf     — Input variables (domain, environment, etc.)
  outputs.tf       — Output values (API endpoint, CloudFront URL, etc.)
  modules/
    networking/    — VPC, subnets, IGW, NAT gateway, security groups
    rds/           — PostgreSQL RDS instance with Multi-AZ support
    s3/            — S3 buckets for SPA hosting and file storage
    cloudfront/    — CloudFront CDN distribution for frontend
    acm/           — SSL/TLS certificates via AWS Certificate Manager
    iam/           — IAM roles, policies, OIDC provider for GitHub Actions
    cognito/       — Cognito User Pool and Google identity provider
    monitoring/    — CloudWatch log groups, metric alarms, dashboards
```

Each module contains:
- `main.tf` — Resource definitions
- `variables.tf` — Module input variables
- `outputs.tf` — Module outputs for cross-module communication
- `README.md` — Module documentation and usage examples

## Configuration

Key variables defined in `variables.tf`:
- `domain` — Custom domain for the application (required)
- `environment` — Environment name (default: "poc")
- `aws_region` — AWS region (default: "us-east-1")
- `db_username` — RDS master username
- `google_client_id` — Google OAuth client ID for authentication

Sensitive variables should be provided via:
- Environment variables: `TF_VAR_<variable_name>`
- Terraform Cloud/Enterprise workspaces
- AWS Secrets Manager (for production)

Example:

```bash
export TF_VAR_db_password="your-secure-password"
export TF_VAR_google_client_secret="your-google-client-secret"
terraform apply -var="domain=tap.provectus.com"
```

## State Management

Terraform state is stored remotely in S3 with the following configuration:
- **Encryption:** Server-side encryption enabled (AES256)
- **Versioning:** Enabled to allow state recovery
- **Locking:** DynamoDB table prevents concurrent modifications
- **Access:** Restricted via IAM policies

To view current state:

```bash
terraform state list
```

To inspect specific resources:

```bash
terraform state show <resource_address>
```

## Security Considerations

- All sensitive variables are marked with `sensitive = true`
- State files are encrypted at rest in S3
- Public access to state bucket is blocked
- IAM policies follow least-privilege principle
- Security groups restrict traffic to minimum required ports
- RDS instances use encryption at rest
- SSL/TLS certificates required for all public endpoints

## Maintenance

### Adding New Modules

1. Create module directory under `modules/`
2. Define resources in `main.tf`
3. Document variables in `variables.tf`
4. Expose outputs in `outputs.tf`
5. Add module documentation in `README.md`
6. Reference module in root `main.tf`

### Updating Infrastructure

1. Make changes to Terraform configuration files
2. Run `terraform validate` to check syntax
3. Run `terraform plan` to preview changes
4. Review plan output carefully
5. Run `terraform apply` to apply changes
6. Verify changes in AWS Console

### Troubleshooting

Enable debug logging:

```bash
export TF_LOG=DEBUG
terraform plan
```

View state locking status:

```bash
aws dynamodb get-item \
  --table-name tap-terraform-locks \
  --key '{"LockID":{"S":"tap-terraform-state-<ACCOUNT_ID>/tap/terraform.tfstate"}}'
```

Force unlock (use only if lock is stuck):

```bash
terraform force-unlock <lock_id>
```

## Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Backend Configuration](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)
- [RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Security.html)
