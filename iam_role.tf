# IAM Role for Lambda
resource "aws_iam_role" "process_void_role" {
  name = "${var.project}-payment-ledger-auditTrail-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_policy" "process_void_policy" {
  name        = "${var.project}-payment-ledger-auditTrail-policy"
  description = "Policy for Lambda to interact with DynamoDB and SQS for payment and ledger audit trail"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        Resource = [
          data.aws_dynamodb_table.transactions_table.arn,
          data.aws_dynamodb_table.transactions_table.arn
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "sqs:SendMessage"
        ],
        Resource = aws_sqs_queue.audit_trail_fifo_queue.arn
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

# Attach Policy to Role
resource "aws_iam_role_policy_attachment" "process_void_policy_attachment" {
  role       = aws_iam_role.process_void_role.name
  policy_arn = aws_iam_policy.process_void_policy.arn
}
