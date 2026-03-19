variable "region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as prefix for resource naming and tagging"
  type        = string
  default     = "lauter"
}

variable "domain" {
  description = "Custom domain for the application (e.g., lauter.provectus.com). Empty string deploys without custom domain using CloudFront default."
  type        = string
  default     = ""

  validation {
    condition     = var.domain == "" || can(regex("^[a-z0-9][a-z0-9-\\.]*[a-z0-9]$", var.domain))
    error_message = "Domain must be empty or a valid DNS name"
  }
}

variable "owner" {
  description = "Team or person responsible for the resources (used in default_tags)"
  type        = string
  default     = "recruitment-team"
}

variable "environment" {
  description = "Environment name (poc, dev, staging, prod) used for resource naming and configuration"
  type        = string
  default     = "poc"

  validation {
    condition     = contains(["poc", "dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: poc, dev, staging, prod"
  }
}

variable "github_repo" {
  description = "GitHub repository in format org/repo for OIDC trust policy"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", var.github_repo))
    error_message = "GitHub repository must be in format org/repo"
  }
}

variable "jwt_secret_key_arn" {
  description = "ARN of the Secrets Manager secret containing the JWT secret key"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "lauter"
}

variable "db_username" {
  description = "Master username for the RDS PostgreSQL instance"
  type        = string
  default     = "lauter_admin"
}

variable "allowed_email_domain" {
  description = "Email domain allowed for user authentication (e.g., provectus.com)"
  type        = string
  default     = "provectus.com"
}

variable "enable_bedrock" {
  description = "Enable Bedrock AI model access for ECS tasks (Phase 2 feature)"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm SNS notifications (empty = no subscription)"
  type        = string
  default     = ""
}

variable "bedrock_model_id_heavy" {
  description = "Bedrock model for complex evaluation tasks (screening, technical, recommendation)"
  type        = string
  default     = "us.anthropic.claude-sonnet-4-6"
}

variable "bedrock_model_id_light" {
  description = "Bedrock model for simpler tasks (CV analysis, feedback generation)"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}
