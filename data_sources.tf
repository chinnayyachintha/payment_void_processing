
# Fetch Current Account Details
data "aws_caller_identity" "current" {}

data "aws_dynamodb_table" "transactions_table" {
  name = var.transactions_table_name
}

data "aws_dynamodb_table" "audit_trail_table" {
  name = var.audit_trail_table_name
}
