variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "ARN of CloudFront distribution for OAC bucket policy. When empty, no policy is created."
  type        = string
  default     = ""
}
