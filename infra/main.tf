terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # IMPORTANT: Replace ACCOUNT_ID with your AWS account ID before initializing
    bucket         = "tap-terraform-state-ACCOUNT_ID"
    key            = "tap/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tap-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
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
}

# S3 Module - Storage buckets for SPA and files
module "s3" {
  source = "./modules/s3"

  project_name                = var.project_name
  environment                 = var.environment
  cloudfront_distribution_arn = module.cloudfront.distribution_arn
}

# ACM Module - SSL/TLS certificate for the domain
module "acm" {
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
  certificate_arn                 = module.acm.certificate_arn
}

# IAM Module - Roles and permissions for ECS, GitHub Actions, and OIDC
module "iam" {
  source = "./modules/iam"

  project_name                 = var.project_name
  environment                  = var.environment
  github_repo                  = var.github_repo
  files_bucket_arn             = module.s3.files_bucket_arn
  spa_bucket_arn               = module.s3.spa_bucket_arn
  db_secret_arn                = module.rds.db_master_secret_arn
  cognito_client_secret_arn    = module.cognito.client_secret_arn
  cognito_user_pool_id_ssm_arn = module.cognito.ssm_user_pool_id_arn
  cognito_client_id_ssm_arn    = module.cognito.ssm_client_id_arn
  cognito_domain_ssm_arn       = module.cognito.ssm_domain_arn
  ecs_cluster_arn              = module.ecs.cluster_arn
  ecs_service_arn              = module.ecs.service_arn
  cloudfront_distribution_arn  = module.cloudfront.distribution_arn
}

# Cognito Module - User Pool with Google OAuth federation
module "cognito" {
  source = "./modules/cognito"

  project_name         = var.project_name
  environment          = var.environment
  domain               = var.domain
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
}

# ECS Module - ECS cluster, ALB, and backend service
module "ecs" {
  source = "./modules/ecs"

  project_name                 = var.project_name
  environment                  = var.environment
  domain                       = var.domain
  vpc_id                       = module.networking.vpc_id
  public_subnet_ids            = module.networking.public_subnet_ids
  private_subnet_ids           = module.networking.private_subnet_ids
  alb_security_group_id        = module.networking.alb_security_group_id
  ecs_security_group_id        = module.networking.ecs_security_group_id
  ecs_execution_role_arn       = module.iam.ecs_execution_role_arn
  ecs_task_role_arn            = module.iam.ecs_task_role_arn
  ecr_repository_url           = module.iam.ecr_repository_url
  certificate_arn              = module.acm.certificate_arn
  db_secret_arn                = module.rds.db_master_secret_arn
  cognito_user_pool_id_ssm_arn = module.cognito.ssm_user_pool_id_arn
  cognito_client_id_ssm_arn    = module.cognito.ssm_client_id_arn
  cognito_domain_ssm_arn       = module.cognito.ssm_domain_arn
  cognito_client_secret_arn    = module.cognito.client_secret_arn
  alb_access_logs_bucket_id    = module.monitoring.alb_access_logs_bucket_id
}

# Monitoring Module - SNS, CloudWatch alarms, ALB logs
module "monitoring" {
  source = "./modules/monitoring"

  project_name            = var.project_name
  environment             = var.environment
  alb_arn_suffix          = module.ecs.alb_arn_suffix
  target_group_arn_suffix = module.ecs.target_group_arn_suffix
  db_instance_id          = module.rds.db_instance_id
}
