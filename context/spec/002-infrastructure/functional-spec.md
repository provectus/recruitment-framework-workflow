# Functional Specification: Infrastructure — AWS Environment & CI/CD

- **Roadmap Item:** Phase 0: Infrastructure (excluding n8n)
- **Status:** Draft
- **Author:** Claude (AI-assisted)

---

## 1. Overview and Rationale (The "Why")

Tap's backend (FastAPI) and frontend (React SPA) currently run only in local development (Docker Compose). Before any Phase 1 product features can reach real users, the application needs a cloud runtime environment and an automated way to deploy code changes to it.

**Problem:** Without cloud infrastructure, the team cannot demo, test with real data, or iterate with recruiters. Without CI/CD, every deployment would be manual and error-prone.

**Desired outcome:** A single POC environment on AWS where both the API and SPA are running, accessible via a custom domain over HTTPS, with automated deployments triggered by pushing code to GitHub. Bedrock (Claude) is enabled for future AI evaluation features.

**Success criteria:**
- Push to `main` → app is automatically built and deployed
- Frontend is served via CloudFront at a custom domain with HTTPS
- Backend API is running on ECS Fargate behind a load balancer, accessible from the frontend
- RDS PostgreSQL is reachable from ECS tasks
- Bedrock Claude model access is enabled in us-east-1
- Health check endpoints return 200

---

## 2. Functional Requirements (The "What")

### 2.1 AWS Environment

The POC needs a single, isolated environment in **us-east-1** within an existing AWS account.

- **Networking:** A dedicated VPC with public and private subnets across at least 2 availability zones. The API and database run in private subnets; only the load balancer and CloudFront are publicly accessible.
  - **Acceptance Criteria:**
    - [ ] VPC is created with public and private subnets in 2+ AZs
    - [ ] Internet Gateway and NAT Gateway are provisioned for outbound access from private subnets
    - [ ] Security groups restrict access: ALB accepts 443 inbound; ECS tasks accept traffic only from ALB; RDS accepts connections only from ECS security group

- **Compute (ECS Fargate):** The FastAPI backend runs as a Fargate service behind an Application Load Balancer.
  - **Acceptance Criteria:**
    - [ ] ECS cluster with a Fargate service running the backend container
    - [ ] Application Load Balancer routes HTTPS traffic to the ECS service
    - [ ] Health check endpoint (`/health`) returns 200 through the ALB
    - [ ] Service auto-restarts on container failure

- **Database (RDS PostgreSQL):** A managed PostgreSQL instance for application data.
  - **Acceptance Criteria:**
    - [ ] RDS PostgreSQL instance is running in a private subnet
    - [ ] ECS tasks can connect to the database
    - [ ] Automated backups are enabled
    - [ ] Database credentials are stored in AWS Secrets Manager (not hardcoded)

- **Storage (S3):** Buckets for SPA static hosting and future file uploads.
  - **Acceptance Criteria:**
    - [ ] S3 bucket for React SPA static assets, served via CloudFront
    - [ ] S3 bucket for application file storage (CVs, transcripts — future use)
    - [ ] Buckets are not publicly accessible (access only via CloudFront OAC or presigned URLs)

- **CDN (CloudFront):** Serves the React SPA globally with HTTPS.
  - **Acceptance Criteria:**
    - [ ] CloudFront distribution serves the SPA from S3
    - [ ] SPA routes (e.g., `/login`, `/candidates`) return `index.html` (SPA fallback behavior)
    - [ ] API requests (`/api/*`) are proxied to the ALB backend — OR — frontend calls the API domain directly via CORS [NEEDS CLARIFICATION: proxy through CloudFront vs separate API domain — to be decided in tech spec]

- **AI (Bedrock):** Claude model access for future evaluation features.
  - **Acceptance Criteria:**
    - [ ] Bedrock model access is enabled for Claude in us-east-1
    - [ ] An IAM role exists that ECS tasks can assume to call Bedrock APIs

- **Authentication (Cognito):** AWS Cognito User Pool with Google as federated identity provider, powering the existing OAuth 2.0 login flow.
  - **Acceptance Criteria:**
    - [ ] Cognito User Pool is created with Google as a federated identity provider
    - [ ] App client is configured for OAuth 2.0 authorization code grant with appropriate callback URLs (`https://api.<domain>/auth/callback`)
    - [ ] Hosted UI domain is provisioned for the Google sign-in redirect
    - [ ] Cognito client ID, client secret, and pool ID are stored in Secrets Manager / SSM and injected into ECS task env vars

- **Monitoring (CloudWatch):** Basic observability for the POC.
  - **Acceptance Criteria:**
    - [ ] ECS service logs are shipped to CloudWatch Logs
    - [ ] ALB access logs are enabled
    - [ ] Basic CloudWatch alarms: ECS service unhealthy, RDS CPU > 80%

### 2.2 Custom Domain & SSL

A custom domain with HTTPS for both frontend and API.

- **Acceptance Criteria:**
  - [ ] ACM certificate issued and validated for the chosen domain
  - [ ] CloudFront distribution uses the custom domain with HTTPS
  - [ ] API is accessible via a subdomain (e.g., `api.<domain>`) or path prefix — with valid HTTPS
  - [ ] DNS records are created (domain-agnostic — specific domain TBD)

### 2.3 CI/CD Pipeline (GitHub Actions)

Automated build and deployment triggered by code changes.

- **Acceptance Criteria:**
  - [ ] Push to `main` triggers deployment of both backend and frontend
  - [ ] Backend pipeline: lint → test → build Docker image → push to ECR → deploy to ECS
  - [ ] Frontend pipeline: lint → build → sync to S3 → invalidate CloudFront cache
  - [ ] Pipeline uses OIDC-based AWS authentication (no long-lived access keys)
  - [ ] Failed lint or tests block deployment
  - [ ] Deployment status is visible in GitHub (check status on PRs)

### 2.4 Infrastructure as Code (Terraform)

All AWS resources are defined in Terraform, version-controlled in the repository.

- **Acceptance Criteria:**
  - [ ] All resources above are defined in Terraform configurations
  - [ ] Terraform state is stored remotely (S3 + DynamoDB locking)
  - [ ] `terraform plan` produces a clean diff from a fresh state
  - [ ] Terraform configurations are in the repository (e.g., `infra/` directory)

---

## 3. Scope and Boundaries

### In-Scope

- Single POC environment in us-east-1
- VPC, subnets, security groups, NAT Gateway
- ECS Fargate cluster + service for FastAPI backend
- RDS PostgreSQL (minimal sizing for POC)
- S3 buckets (SPA hosting + file storage)
- CloudFront distribution for SPA
- ACM certificate + custom domain DNS records
- Cognito User Pool with Google IdP, app client, hosted UI domain
- Bedrock Claude model access enablement
- CloudWatch Logs + basic alarms
- GitHub Actions CI/CD pipelines (backend + frontend)
- Terraform IaC for all resources
- OIDC-based GitHub → AWS authentication

### Out-of-Scope

- **n8n instance setup** — deferred, will be addressed in a separate spec
- **Multiple environments** (staging, production) — single POC env only for now
- **WAF / advanced security** — not needed for internal POC
- **Auto-scaling policies** — fixed task count is sufficient for POC
- **Custom monitoring dashboards** — basic CloudWatch alarms only
- **All Phase 1+ features** (Candidate List, Interview Library, CV Upload, Barley Integration, Lever Integration, etc.)
- **All Phase 2 features** (Screening Summary, Technical Evaluation, Recommendation)
- **All Phase 3 features** (Lever Write, Candidate Feedback)
