output "spa_bucket_id" {
  description = "SPA bucket name/ID"
  value       = aws_s3_bucket.spa.id
}

output "spa_bucket_arn" {
  description = "SPA bucket ARN"
  value       = aws_s3_bucket.spa.arn
}

output "spa_bucket_regional_domain_name" {
  description = "SPA bucket regional domain name for CloudFront origin configuration"
  value       = aws_s3_bucket.spa.bucket_regional_domain_name
}

output "files_bucket_id" {
  description = "Files bucket name/ID"
  value       = aws_s3_bucket.files.id
}

output "files_bucket_arn" {
  description = "Files bucket ARN"
  value       = aws_s3_bucket.files.arn
}
