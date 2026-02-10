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
