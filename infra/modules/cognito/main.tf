# Cognito User Pool for authentication
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Disable self-signup - users come through Google federation
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  # Account recovery via email only
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Password policy (used for admin-created users)
  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # User pool schema
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = false

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  tags = {
    Name = "${var.project_name}-users"
  }
}

# Google Identity Provider for federated authentication
resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "openid email profile"
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
  }
}

# User Pool App Client for web application
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project_name}-web-client"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = true

  # Supported identity providers
  supported_identity_providers = ["Google"]

  # OAuth configuration
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  # Callback and logout URLs
  callback_urls = ["https://api.${var.domain}/auth/callback"]
  logout_urls   = ["https://${var.domain}/login"]

  # Auth flows
  explicit_auth_flows = ["ALLOW_REFRESH_TOKEN_AUTH"]

  # Token validity
  refresh_token_validity = 7
  access_token_validity  = 60
  id_token_validity      = 60

  token_validity_units {
    refresh_token = "days"
    access_token  = "minutes"
    id_token      = "minutes"
  }

  # Prevent resource destruction before plan
  prevent_user_existence_errors = "ENABLED"
}

# Cognito Hosted UI domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-auth"
  user_pool_id = aws_cognito_user_pool.main.id
}

# SSM Parameter: User Pool ID
resource "aws_ssm_parameter" "user_pool_id" {
  name        = "/tap/cognito/user_pool_id"
  description = "Cognito User Pool ID for Tap application"
  type        = "String"
  value       = aws_cognito_user_pool.main.id

  tags = {
    Name = "${var.project_name}-cognito-user-pool-id"
  }
}

# SSM Parameter: Client ID
resource "aws_ssm_parameter" "client_id" {
  name        = "/tap/cognito/client_id"
  description = "Cognito App Client ID for Tap application"
  type        = "String"
  value       = aws_cognito_user_pool_client.web.id

  tags = {
    Name = "${var.project_name}-cognito-client-id"
  }
}

# SSM Parameter: Cognito Domain
resource "aws_ssm_parameter" "domain" {
  name        = "/tap/cognito/domain"
  description = "Cognito Hosted UI domain URL for Tap application"
  type        = "String"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"

  tags = {
    Name = "${var.project_name}-cognito-domain"
  }
}

# Secrets Manager: Client Secret
resource "aws_secretsmanager_secret" "client_secret" {
  name                    = "${var.project_name}/cognito/client_secret"
  description             = "Cognito App Client Secret for Tap application"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-cognito-client-secret"
  }
}

resource "aws_secretsmanager_secret_version" "client_secret" {
  secret_id     = aws_secretsmanager_secret.client_secret.id
  secret_string = aws_cognito_user_pool_client.web.client_secret
}

# Data source for current region
data "aws_region" "current" {}
