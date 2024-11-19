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

# Name of the DynamoDB Transactions Table
variable "transactions_table_name" {
  type        = string
  description = "Name of the DynamoDB Transactions Table"
}

# Name of the DynamoDB Audit Trail Table
variable "audit_trail_table_name" {
  type        = string
  description = "Name of the DynamoDB Audit Trail Table"
}
