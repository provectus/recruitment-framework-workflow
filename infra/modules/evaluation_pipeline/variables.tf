variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "rds_security_group_id" {
  type = string
}

variable "rds_instance_address" {
  type = string
}

variable "rds_instance_port" {
  type = number
}

variable "db_name" {
  type = string
}

variable "db_username" {
  type = string
}

variable "db_master_secret_arn" {
  type = string
}

variable "files_bucket_arn" {
  type = string
}

variable "files_bucket_id" {
  type = string
}

variable "bedrock_model_id_heavy" {
  type = string
}

variable "bedrock_model_id_light" {
  type = string
}

variable "lambdas_source_path" {
  description = "Absolute path to the app/lambdas directory"
  type        = string
}
