output "db_instance_endpoint" {
  description = "Connection endpoint (host:port)"
  value       = aws_db_instance.this.endpoint
}

output "db_instance_address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.this.address
}

output "db_instance_port" {
  description = "Port number of the RDS instance"
  value       = aws_db_instance.this.port
}

output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.this.id
}

output "db_master_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the master password"
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}
