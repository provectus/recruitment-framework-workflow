output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = aws_sns_topic.alerts.arn
}

output "alb_access_logs_bucket_id" {
  description = "Name of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.id
}

output "alb_access_logs_bucket_arn" {
  description = "ARN of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.arn
}

output "ecs_unhealthy_hosts_alarm_arn" {
  description = "ARN of the ECS unhealthy hosts CloudWatch alarm"
  value       = aws_cloudwatch_metric_alarm.ecs_unhealthy_hosts.arn
}

output "rds_high_cpu_alarm_arn" {
  description = "ARN of the RDS high CPU CloudWatch alarm"
  value       = aws_cloudwatch_metric_alarm.rds_high_cpu.arn
}
