variable "project_name" {
  description = "Project name used for resource naming"
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

variable "ecs_cluster_name" {
  description = "ECS cluster name for CloudWatch alarm dimensions"
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name for CloudWatch alarm dimensions"
  type        = string
}

variable "alert_email" {
  description = "Email address for SNS alarm notifications (empty = no subscription)"
  type        = string
  default     = ""
}
