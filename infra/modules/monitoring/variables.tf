variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch alarm dimensions"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for CloudWatch alarm dimensions"
  type        = string
}

variable "db_instance_id" {
  description = "RDS instance identifier for CloudWatch alarm dimensions"
  type        = string
}
