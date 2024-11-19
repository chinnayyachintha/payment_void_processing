resource "aws_dynamodb_table" "transactions_table" {
  name         = "${var.project}-TransactionsTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "TransactionID"

  attribute {
    name = "TransactionID"
    type = "S"
  }

  tags = {
    Name = "${var.project}-TransactionsTable"
  }
}

resource "aws_dynamodb_table" "audit_trail_table" {
  name         = "${var.project}-AuditTrailTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "AuditID"

  attribute {
    name = "AuditID"
    type = "S"
  }

  tags = {
    Name = "${var.project}-AuditTrailTable"
  }
}
