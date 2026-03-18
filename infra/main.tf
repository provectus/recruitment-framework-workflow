locals {
  use_custom_domain = var.domain != ""
}

# Google OAuth credentials from Secrets Manager
data "aws_secretsmanager_secret_version" "google_client_id" {
  secret_id = "${var.project_name}/google-oauth/client-id"
}

data "aws_secretsmanager_secret_version" "google_client_secret" {
  secret_id = "${var.project_name}/google-oauth/client-secret"
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      Owner       = var.owner
      ManagedBy   = "Terraform"
    }
  }
}

# Networking Module - VPC, subnets, security groups
module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
}

# RDS Module - PostgreSQL database
module "rds" {
  source = "./modules/rds"

  project_name          = var.project_name
  environment           = var.environment
  private_subnet_ids    = module.networking.private_subnet_ids
  rds_security_group_id = module.networking.rds_security_group_id
  db_name               = var.db_name
  db_username           = var.db_username
}

# S3 Module - Storage buckets for SPA and files
module "s3" {
  source = "./modules/s3"

  project_name                = var.project_name
  environment                 = var.environment
  cloudfront_distribution_arn = module.cloudfront.distribution_arn
  files_cors_allowed_origins = compact([
    local.use_custom_domain ? "https://${var.domain}" : "",
    "https://${module.cloudfront.distribution_domain_name}",
  ])
}

# ACM Module - SSL/TLS certificate for the domain (skipped when no custom domain)
module "acm" {
  count  = local.use_custom_domain ? 1 : 0
  source = "./modules/acm"

  project_name = var.project_name
  environment  = var.environment
  domain       = var.domain
}

# CloudFront Module - CDN distribution for SPA
module "cloudfront" {
  source = "./modules/cloudfront"

  project_name                    = var.project_name
  environment                     = var.environment
  domain                          = var.domain
  spa_bucket_id                   = module.s3.spa_bucket_id
  spa_bucket_regional_domain_name = module.s3.spa_bucket_regional_domain_name
  certificate_arn                 = local.use_custom_domain ? module.acm[0].certificate_arn : ""
  web_acl_arn                     = module.waf.cloudfront_web_acl_arn
  alb_domain_name                 = module.ecs.alb_dns_name
  access_logs_bucket_domain_name  = module.s3.cloudfront_logs_bucket_domain_name
}

# IAM Module - Roles and permissions for ECS, GitHub Actions, and OIDC
module "iam" {
  source = "./modules/iam"

  project_name                 = var.project_name
  environment                  = var.environment
  region                       = var.region
  github_repo                  = var.github_repo
  files_bucket_arn             = module.s3.files_bucket_arn
  spa_bucket_arn               = module.s3.spa_bucket_arn
  db_secret_arn                = module.rds.db_master_secret_arn
  cognito_client_secret_arn    = module.cognito.client_secret_arn
  cognito_user_pool_id_ssm_arn = module.cognito.ssm_user_pool_id_arn
  cognito_client_id_ssm_arn    = module.cognito.ssm_client_id_arn
  cognito_domain_ssm_arn       = module.cognito.ssm_domain_arn
  jwt_secret_key_arn           = var.jwt_secret_key_arn
  ecs_cluster_arn              = module.ecs.cluster_arn
  ecs_service_arn              = module.ecs.service_arn
  cloudfront_distribution_arn  = module.cloudfront.distribution_arn
  enable_bedrock               = var.enable_bedrock
  enable_ecs_exec              = var.environment != "prod"
  evaluation_event_bus_arn     = module.evaluation_pipeline.event_bus_arn
}

# Evaluation Pipeline Module - EventBridge, Lambdas, Step Functions
module "evaluation_pipeline" {
  source = "./modules/evaluation_pipeline"

  project_name           = var.project_name
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = module.networking.private_subnet_ids
  rds_security_group_id  = module.networking.rds_security_group_id
  rds_instance_address   = module.rds.db_instance_address
  rds_instance_port      = module.rds.db_instance_port
  db_name                = var.db_name
  db_username            = var.db_username
  db_master_secret_arn   = module.rds.db_master_secret_arn
  files_bucket_arn       = module.s3.files_bucket_arn
  files_bucket_id        = module.s3.files_bucket_id
  bedrock_model_id_heavy = var.bedrock_model_id_heavy
  bedrock_model_id_light = var.bedrock_model_id_light
  lambdas_source_path    = "${path.module}/../app/lambdas"
}

# Cognito Module - User Pool with Google OAuth federation
module "cognito" {
  source = "./modules/cognito"

  project_name         = var.project_name
  environment          = var.environment
  app_url              = local.use_custom_domain ? var.domain : module.cloudfront.distribution_domain_name
  google_client_id     = data.aws_secretsmanager_secret_version.google_client_id.secret_string
  google_client_secret = data.aws_secretsmanager_secret_version.google_client_secret.secret_string
}

# WAF Module - Web Application Firewall ACLs for CloudFront and ALB
module "waf" {
  source = "./modules/waf"

  project_name = var.project_name
  environment  = var.environment
}

# ECS Module - ECS cluster, ALB, and backend service
module "ecs" {
  source = "./modules/ecs"

  project_name                 = var.project_name
  environment                  = var.environment
  debug                        = !local.use_custom_domain
  domain                       = var.domain
  vpc_id                       = module.networking.vpc_id
  public_subnet_ids            = module.networking.public_subnet_ids
  private_subnet_ids           = module.networking.private_subnet_ids
  alb_security_group_id        = module.networking.alb_security_group_id
  ecs_security_group_id        = module.networking.ecs_security_group_id
  ecs_execution_role_arn       = module.iam.ecs_execution_role_arn
  ecs_task_role_arn            = module.iam.ecs_task_role_arn
  ecr_repository_url           = module.iam.ecr_repository_url
  certificate_arn              = local.use_custom_domain ? module.acm[0].certificate_arn : ""
  db_secret_arn                = module.rds.db_master_secret_arn
  db_host                      = module.rds.db_instance_address
  db_port                      = module.rds.db_instance_port
  db_name                      = var.db_name
  db_username                  = var.db_username
  cognito_user_pool_id_ssm_arn = module.cognito.ssm_user_pool_id_arn
  cognito_client_id_ssm_arn    = module.cognito.ssm_client_id_arn
  cognito_domain_ssm_arn       = module.cognito.ssm_domain_arn
  cognito_client_secret_arn    = module.cognito.client_secret_arn
  jwt_secret_key_arn           = var.jwt_secret_key_arn
  cognito_redirect_uri         = "https://${local.use_custom_domain ? var.domain : module.cloudfront.distribution_domain_name}/api/auth/callback"
  files_bucket_name            = module.s3.files_bucket_id
  allowed_email_domain         = var.allowed_email_domain
  alb_access_logs_bucket_id    = module.monitoring.alb_access_logs_bucket_id
  evaluation_event_bus_name    = module.evaluation_pipeline.event_bus_name
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = module.ecs.alb_arn
  web_acl_arn  = module.waf.alb_web_acl_arn
}

# Monitoring Module - SNS, CloudWatch alarms, ALB logs
module "monitoring" {
  source = "./modules/monitoring"

  project_name            = var.project_name
  environment             = var.environment
  alb_arn_suffix          = module.ecs.alb_arn_suffix
  target_group_arn_suffix = module.ecs.target_group_arn_suffix
  db_instance_id          = module.rds.db_instance_id
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_service_name        = module.ecs.service_name
  alert_email             = var.alert_email
}
