variable "project_name" {
  description = "Project name used as prefix for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "domain" {
  description = "Custom domain for the application (empty = placeholder callbacks, use DEBUG mode)"
  type        = string
  default     = ""
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
