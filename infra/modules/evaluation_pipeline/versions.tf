terraform {
  required_version = ">= 1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.33.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "= 2.7.1"
    }
    null = {
      source  = "hashicorp/null"
      version = "= 3.2.4"
    }
  }
}
