output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "client_id" {
  description = "Cognito App Client ID"
  value       = aws_cognito_user_pool_client.web.id
}

output "user_pool_domain" {
  description = "Full Cognito Hosted UI domain URL"
  value       = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

output "ssm_user_pool_id_arn" {
  description = "SSM Parameter ARN for User Pool ID"
  value       = aws_ssm_parameter.user_pool_id.arn
}

output "ssm_client_id_arn" {
  description = "SSM Parameter ARN for App Client ID"
  value       = aws_ssm_parameter.client_id.arn
}

output "ssm_domain_arn" {
  description = "SSM Parameter ARN for Cognito domain URL"
  value       = aws_ssm_parameter.domain.arn
}

output "client_secret_arn" {
  description = "Secrets Manager ARN for App Client Secret"
  value       = aws_secretsmanager_secret.client_secret.arn
}
