output "event_bus_name" {
  description = "Name of the evaluation EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.evaluation.name
}

output "event_bus_arn" {
  description = "ARN of the evaluation EventBridge custom event bus"
  value       = aws_cloudwatch_event_bus.evaluation.arn
}
