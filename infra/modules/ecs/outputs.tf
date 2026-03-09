output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.backend.name
}

output "service_arn" {
  description = "ARN of the ECS service"
  value       = aws_ecs_service.backend.id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_zone_id" {
  description = "Zone ID of the ALB for Route53 alias records"
  value       = aws_lb.main.zone_id
}

output "target_group_arn" {
  description = "ARN of the ALB target group"
  value       = aws_lb_target_group.backend.arn
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.backend.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for ECS"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "alb_arn_suffix" {
  description = "ARN suffix of the ALB for CloudWatch metrics"
  value       = aws_lb.main.arn_suffix
}

output "target_group_arn_suffix" {
  description = "ARN suffix of the target group for CloudWatch metrics"
  value       = aws_lb_target_group.backend.arn_suffix
}
