variable "project_name" {
  description = "Project name used as prefix for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (poc, dev, staging, prod)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository in format org/repo for OIDC trust policy"
  type        = string
}

variable "files_bucket_arn" {
  description = "ARN of the S3 bucket for file uploads (CVs, transcripts)"
  type        = string
}

variable "spa_bucket_arn" {
  description = "ARN of the S3 bucket for the React SPA static files"
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the Secrets Manager secret containing DB credentials"
  type        = string
}

variable "cognito_client_secret_arn" {
  description = "ARN of the Secrets Manager secret containing Cognito client secret"
  type        = string
}

variable "cognito_user_pool_id_ssm_arn" {
  description = "ARN of the SSM parameter containing Cognito User Pool ID"
  type        = string
}

variable "cognito_client_id_ssm_arn" {
  description = "ARN of the SSM parameter containing Cognito Client ID"
  type        = string
}

variable "cognito_domain_ssm_arn" {
  description = "ARN of the SSM parameter containing Cognito domain URL"
  type        = string
}

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster for GitHub Actions policy scoping"
  type        = string
}

variable "ecs_service_arn" {
  description = "ARN of the ECS service for GitHub Actions policy scoping"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution for GitHub Actions policy scoping"
  type        = string
}
