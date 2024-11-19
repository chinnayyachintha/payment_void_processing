resource "aws_lambda_function" "retrieve_ledger_entries_void" {
  function_name = "${var.project}-RetrieveLedgerEntries"
  runtime       = "python3.9"
  handler       = "retrieve_ledger_lambda.lambda_handler" # Matches the Python script
  role          = aws_iam_role.process_void_role.arn

  filename = "lambda_function/retrieve_ledger_entries.zip" # Ensure this matches the zip file location

  environment {
    variables = {
      TRANSACTIONS_TABLE = data.aws_dynamodb_table.transactions_table.name
    }
  }

  # Add dependencies for proper ordering
  depends_on = [
    data.aws_dynamodb_table.transactions_table
  ]
}

resource "aws_lambda_function" "persist_payment_ledger_void" {
  function_name = "${var.project}-PersistPaymentLedger"
  runtime       = "python3.9"
  handler       = "persist_ledger_lambda.lambda_handler" # Matches the Python script
  role          = aws_iam_role.process_void_role.arn

  filename = "lambda_function/persist_payment_ledger.zip" # Ensure this matches the zip file location

  environment {
    variables = {
      TRANSACTIONS_TABLE = data.aws_dynamodb_table.transactions_table.name
    }
  }

  # Add dependencies for proper ordering
  depends_on = [
    data.aws_dynamodb_table.transactions_table
  ]
}

resource "aws_lambda_function" "persist_audit_trail_void" {
  function_name = "${var.project}-PersistAuditTrail"
  runtime       = "python3.9"
  handler       = "audit_trail_lambda.lambda_handler" # Matches the Python script
  role          = aws_iam_role.process_void_role.arn

  filename = "lambda_function/persist_audit_trail.zip" # Ensure this matches the zip file location

  environment {
    variables = {
      AUDIT_TRAIL_TABLE = data.aws_dynamodb_table.audit_trail_table.name,
      FIFO_QUEUE_URL    = aws_sqs_queue.audit_trail_fifo_queue.id # Optional for SQS FIFO integration
    }
  }

  # Add dependencies for proper ordering
  depends_on = [
    data.aws_dynamodb_table.audit_trail_table,
    aws_sqs_queue.audit_trail_fifo_queue
  ]
}