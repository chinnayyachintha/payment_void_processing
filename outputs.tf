# Outputs for DynamoDB Tables
output "transactions_table_name" {
  description = "Name of the DynamoDB Transactions Table"
  value       = data.aws_dynamodb_table.transactions_table.name
}

output "audit_trail_table_name" {
  description = "Name of the DynamoDB Audit Trail Table"
  value       = data.aws_dynamodb_table.audit_trail_table.name
}

output "transactions_table_arn" {
  description = "ARN of the DynamoDB Transactions Table"
  value       = data.aws_dynamodb_table.transactions_table.arn
}

output "audit_trail_table_arn" {
  description = "ARN of the DynamoDB Audit Trail Table"
  value       = data.aws_dynamodb_table.audit_trail_table.arn
}

# Outputs for Lambda Functions
output "retrieve_ledger_entries_function_arn" {
  description = "ARN of the RetrieveLedgerEntries Lambda function"
  value       = aws_lambda_function.retrieve_ledger_entries_void.arn
}

output "persist_payment_ledger_function_arn" {
  description = "ARN of the PersistPaymentLedger Lambda function"
  value       = aws_lambda_function.persist_payment_ledger_void.arn
}

output "persist_audit_trail_function_arn" {
  description = "ARN of the PersistAuditTrail Lambda function"
  value       = aws_lambda_function.persist_audit_trail_void.arn
}

output "retrieve_ledger_entries_function_name" {
  description = "Name of the RetrieveLedgerEntries Lambda function"
  value       = aws_lambda_function.retrieve_ledger_entries_void.function_name
}

output "persist_payment_ledger_function_name" {
  description = "Name of the PersistPaymentLedger Lambda function"
  value       = aws_lambda_function.persist_payment_ledger_void.function_name
}

output "persist_audit_trail_function_name" {
  description = "Name of the PersistAuditTrail Lambda function"
  value       = aws_lambda_function.persist_audit_trail_void.function_name
}

# Outputs for IAM Role
output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.process_void_role.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.process_void_role.name
}

# Outputs for SQS Queue
output "audit_trail_fifo_queue_name" {
  description = "Name of the SQS FIFO queue for audit trail"
  value       = aws_sqs_queue.audit_trail_fifo_queue.name
}

output "audit_trail_fifo_queue_url" {
  description = "URL of the SQS FIFO queue for audit trail"
  value       = aws_sqs_queue.audit_trail_fifo_queue.id
}

output "audit_trail_fifo_queue_arn" {
  description = "ARN of the SQS FIFO queue for audit trail"
  value       = aws_sqs_queue.audit_trail_fifo_queue.arn
}
