# Inserts audit trail records into the AuditTrailTable in DynamoDB.
# Optionally uses an SQS FIFO queue to handle ordered processing.
# Includes IAM permissions for DynamoDB writes and SQS operations.

import boto3
import logging
import os
import uuid
import json
from botocore.exceptions import ClientError
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

# Environment variables
AUDIT_TRAIL_TABLE_NAME = os.getenv("AUDIT_TRAIL_TABLE")
FIFO_QUEUE_URL = os.getenv("FIFO_QUEUE_URL")  # Optional FIFO queue URL
REGION = os.getenv("AWS_REGION", "us-east-1")

# DynamoDB table reference
audit_trail_table = dynamodb.Table(AUDIT_TRAIL_TABLE_NAME)


def persist_to_dynamodb(audit_entry):
    """Persist audit entry directly to DynamoDB."""
    try:
        audit_trail_table.put_item(Item=audit_entry)
        logger.info(f"Successfully saved audit entry to DynamoDB: {audit_entry}")
    except ClientError as e:
        logger.error(f"Failed to persist to DynamoDB: {e.response['Error']['Message']}")
        raise


def send_to_sqs_fifo(audit_entry):
    """Send audit entry to SQS FIFO queue for ordered processing."""
    try:
        sqs.send_message(
            QueueUrl=FIFO_QUEUE_URL,
            MessageBody=json.dumps(audit_entry),
            MessageGroupId=audit_entry["TransactionID"],  # Group by transaction ID
            MessageDeduplicationId=audit_entry["AuditID"],  # Ensure deduplication
        )
        logger.info(f"Successfully sent audit entry to SQS FIFO: {audit_entry}")
    except ClientError as e:
        logger.error(f"Failed to send to SQS FIFO: {e.response['Error']['Message']}")
        raise


def validate_event(event):
    """Validate the incoming event payload."""
    required_fields = ["transactionId", "voidTransactionId", "actor", "action", "details"]
    missing_fields = [field for field in required_fields if field not in event]

    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_message)
        raise ValueError(error_message)


def lambda_handler(event, context):
    """
    Lambda entry point for persisting audit trails.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Step 1: Validate input
        validate_event(event)

        # Step 2: Construct audit trail entry
        audit_entry = {
            "AuditID": str(uuid.uuid4()),  # Unique identifier for the audit log
            "TransactionID": event["transactionId"],
            "VoidTransactionID": event["voidTransactionId"],
            "Actor": event["actor"],
            "Action": event["action"],
            "Details": event["details"],
            "Timestamp": datetime.utcnow().isoformat(),  # Use ISO 8601 format
        }

        # Step 3: Persist audit trail
        if FIFO_QUEUE_URL:  # If SQS FIFO is configured
            send_to_sqs_fifo(audit_entry)
        else:  # Directly save to DynamoDB
            persist_to_dynamodb(audit_entry)

        # Step 4: Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Audit trail successfully recorded",
                "auditEntry": audit_entry,
            }),
        }

    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(ve)}),
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
