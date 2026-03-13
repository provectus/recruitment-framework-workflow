terraform {
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
}
