variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
}

variable "rate_limit" {
  description = "Maximum requests per 5-minute period per IP"
  type        = number
  default     = 2000
}
