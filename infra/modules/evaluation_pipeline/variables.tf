variable "project_name" {
  description = "Project name used as prefix for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Lambda security group"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Lambda VPC attachment"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group ID for RDS access from Lambdas"
  type        = string
}

variable "rds_instance_address" {
  description = "RDS instance hostname"
  type        = string
}

variable "rds_instance_port" {
  description = "RDS instance port"
  type        = number
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
}

variable "db_master_secret_arn" {
  description = "ARN of Secrets Manager secret containing the RDS master password"
  type        = string
}

variable "files_bucket_arn" {
  description = "ARN of the S3 bucket storing candidate files"
  type        = string
}

variable "files_bucket_id" {
  description = "Name/ID of the S3 bucket storing candidate files"
  type        = string
}

variable "bedrock_model_id_heavy" {
  description = "Bedrock model for complex evaluation tasks (screening, technical, recommendation)"
  type        = string
}

variable "bedrock_model_id_light" {
  description = "Bedrock model for simpler tasks (CV analysis, feedback generation)"
  type        = string
}

variable "lambdas_source_path" {
  description = "Absolute path to the app/lambdas directory"
  type        = string
}
