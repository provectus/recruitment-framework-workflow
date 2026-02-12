variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
}

variable "domain" {
  description = "Custom domain for CloudFront distribution"
  type        = string
}

variable "spa_bucket_id" {
  description = "S3 bucket ID for SPA origin"
  type        = string
}

variable "spa_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  type        = string
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}
