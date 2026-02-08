terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Using local state — create S3 bucket and uncomment for remote state:
  # backend "s3" {
  #   bucket = "carms-explorer-tfstate"
  #   key    = "terraform.tfstate"
  #   region = "ca-central-1"
  # }
}

provider "aws" {
  region = var.aws_region
}
