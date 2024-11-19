# AWS Region where resources will be deployed
variable "aws_region" {
  type        = string
  description = "AWS Region to deploy resources"
}

# Project name
variable "project" {
  type        = string
  description = "Project name"
}