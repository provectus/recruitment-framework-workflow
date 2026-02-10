output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role for pulling images and writing logs"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role for application runtime permissions"
  value       = aws_iam_role.ecs_task.arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions role for CI/CD deployments"
  value       = aws_iam_role.github_actions.arn
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for backend container images"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.backend.arn
}
