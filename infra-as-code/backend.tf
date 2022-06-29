  terraform {
  backend "s3" {
    bucket      = "gpass0s-aws-cicd-pipeline"
    key         = "terraform-iot-processing/terraform.tfstate"
    region      = "us-east-1"
    encrypt     = true
  }
}

provider "aws" {
    region = "us-east-1"
}