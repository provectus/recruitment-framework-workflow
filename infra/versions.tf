terraform {
  required_version = "= 1.14.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.33.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "= 2.7.1"
    }
  }

  backend "s3" {
    # IMPORTANT: Replace ACCOUNT_ID with your AWS account ID before initializing
    bucket         = "lauter-terraform-state-ACCOUNT_ID"
    key            = "lauter/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "lauter-terraform-locks"
    encrypt        = true
  }
}
