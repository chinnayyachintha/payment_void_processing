
# Fetch Current Account Details
data "aws_caller_identity" "current" {}

data "aws_dynamodb_table" "transactions_table" {
  name = "ProcessPaymentLedger"
}

data "aws_dynamodb_table" "audit_trail_table" {
  name = "ProcessPaymentAuditTrail"
}
