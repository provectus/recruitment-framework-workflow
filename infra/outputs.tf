# Networking outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = module.networking.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = module.networking.ecs_security_group_id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = module.networking.rds_security_group_id
}

# Database
output "db_instance_endpoint" {
  description = "Connection endpoint for the RDS instance"
  value       = module.rds.db_instance_endpoint
}

output "db_instance_address" {
  description = "Hostname of the RDS instance"
  value       = module.rds.db_instance_address
}

output "db_master_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the DB master password"
  value       = module.rds.db_master_secret_arn
  sensitive   = true
}

# Storage
output "spa_bucket_id" {
  description = "Name of the SPA S3 bucket"
  value       = module.s3.spa_bucket_id
}

output "spa_bucket_arn" {
  description = "ARN of the SPA S3 bucket"
  value       = module.s3.spa_bucket_arn
}

output "files_bucket_id" {
  description = "Name of the files S3 bucket"
  value       = module.s3.files_bucket_id
}

output "files_bucket_arn" {
  description = "ARN of the files S3 bucket"
  value       = module.s3.files_bucket_arn
}

# CDN outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for the React SPA"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain_name
}

# Compute outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

# Certificate outputs
output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = module.acm.certificate_arn
}

output "domain_validation_records" {
  description = "DNS validation records to create for ACM certificate"
  value       = module.acm.domain_validation_options
}

# IAM outputs
output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = module.iam.ecs_execution_role_arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = module.iam.ecs_task_role_arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions role for CI/CD"
  value       = module.iam.github_actions_role_arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for backend images"
  value       = module.iam.ecr_repository_url
}

# Auth outputs
# output "cognito_user_pool_id" {
#   description = "ID of the Cognito user pool"
#   value       = module.cognito.user_pool_id
# }

# output "cognito_domain" {
#   description = "Full Cognito Hosted UI domain URL"
#   value       = module.cognito.user_pool_domain
# }

# Monitoring outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = module.monitoring.sns_topic_arn
}

output "alb_access_logs_bucket_id" {
  description = "Name of the S3 bucket for ALB access logs"
  value       = module.monitoring.alb_access_logs_bucket_id
}
