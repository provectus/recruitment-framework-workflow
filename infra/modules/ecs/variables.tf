variable "project_name" {
  description = "Name of the project (e.g., tap)"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
}

variable "domain" {
  description = "Primary domain for the application"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for the Application Load Balancer"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecr_repository_url" {
  description = "URL of the ECR repository for backend images"
  type        = string
}

variable "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the database connection URL"
  type        = string
}

variable "cognito_user_pool_id_ssm_arn" {
  description = "ARN of the SSM parameter for Cognito User Pool ID"
  type        = string
  default     = ""
}

variable "cognito_client_id_ssm_arn" {
  description = "ARN of the SSM parameter for Cognito Client ID"
  type        = string
  default     = ""
}

variable "cognito_domain_ssm_arn" {
  description = "ARN of the SSM parameter for Cognito Domain"
  type        = string
  default     = ""
}

variable "cognito_client_secret_arn" {
  description = "ARN of the Secrets Manager secret for Cognito Client Secret"
  type        = string
  default     = ""
}

variable "alb_access_logs_bucket_id" {
  description = "S3 bucket ID for ALB access logs"
  type        = string
  default     = ""
}
