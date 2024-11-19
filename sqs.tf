resource "aws_sqs_queue" "audit_trail_fifo_queue" {
  name                        = "${var.project}-AuditTrailQueue.fifo"
  fifo_queue                  = true
  content_based_deduplication = true

  tags = {
    Name = "${var.project}-AuditTrailQueue"
  }
}