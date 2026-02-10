variable "region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as prefix for resource naming and tagging"
  type        = string
  default     = "tap"
}

variable "domain" {
  description = "Custom domain for the application (e.g., tap.provectus.com)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-\\.]*[a-z0-9]$", var.domain))
    error_message = "Domain must be a valid DNS name"
  }
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

variable "google_client_id" {
  description = "Google OAuth 2.0 client ID for Cognito Google federation"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth 2.0 client secret for Cognito Google federation"
  type        = string
  sensitive   = true
}
