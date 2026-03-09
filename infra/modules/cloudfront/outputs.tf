output "distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.spa.id
}

output "distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.spa.arn
}

output "distribution_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.spa.domain_name
}

output "oac_id" {
  description = "CloudFront Origin Access Control ID"
  value       = aws_cloudfront_origin_access_control.spa.id
}
