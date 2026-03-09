output "cloudfront_web_acl_arn" {
  description = "ARN of the CloudFront WAF ACL"
  value       = aws_wafv2_web_acl.cloudfront.arn
}

output "alb_web_acl_arn" {
  description = "ARN of the ALB WAF ACL"
  value       = aws_wafv2_web_acl.alb.arn
}
