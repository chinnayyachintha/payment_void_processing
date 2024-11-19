import boto3
import logging
import time
import json
import os
from botocore.exceptions import ClientError

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
sqs = boto3.client('sqs')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Fetch environment variables
TRANSACTIONS_TABLE = os.environ.get('TRANSACTIONS_TABLE')
AUDIT_TRAIL_TABLE = os.environ.get('AUDIT_TRAIL_TABLE')
FIFO_QUEUE_URL = os.environ.get('FIFO_QUEUE_URL')

if not TRANSACTIONS_TABLE or not AUDIT_TRAIL_TABLE or not FIFO_QUEUE_URL:
    logger.error("Missing required environment variables.")
    raise ValueError("Environment variables TRANSACTIONS_TABLE, AUDIT_TRAIL_TABLE, and FIFO_QUEUE_URL must be set.")

def get_transaction(transaction_id):
    """Retrieve the original transaction from DynamoDB."""
    try:
        response = dynamodb.get_item(
            TableName=TRANSACTIONS_TABLE,
            Key={'TransactionID': {'S': transaction_id}}
        )
        if 'Item' not in response:
            logger.error(f"Transaction {transaction_id} not found in DynamoDB.")
            return None
        return response['Item']
    except ClientError as e:
        logger.error(f"DynamoDB get_item failed for transaction {transaction_id}: {e.response['Error']['Message']}")
        raise e

def validate_transaction(transaction):
    """Validate if the transaction is eligible for voiding or refunding."""
    status = transaction.get('status', {}).get('S')

    # Check if status is PAYMENT-SUCCESS (finalized transaction)
    if status == 'PAYMENT-SUCCESS':
        error_message = f"Transaction {transaction['TransactionID']['S']} cannot be voided, status is {status}. Consider issuing a refund."
        logger.error(error_message)
        raise ValueError(error_message)

    # You can add additional checks for other status like COMPLETED or PROCESSING if required
    if status != 'COMPLETED' and status != 'PROCESSING':
        error_message = f"Transaction {transaction['TransactionID']['S']} cannot be voided, status is {status}"
        logger.error(error_message)
        raise ValueError(error_message)
    
    return True

def create_refund_transaction(transaction, refund_amount, reason):
    """Create a refund transaction for a completed payment."""
    try:
        new_transaction = {
            'TransactionID': {'S': f"{transaction['TransactionID']['S']}-REFUND"},
            'Status': {'S': 'Refunded'},
            'OriginalTransactionID': {'S': transaction['TransactionID']['S']},
            'Amount': {'N': str(-refund_amount)},  # Negative value for refund
            'Reason': {'S': reason},
            'Timestamp': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ')},  # Current time in UTC
        }

        dynamodb.put_item(
            TableName=TRANSACTIONS_TABLE,
            Item=new_transaction
        )
        logger.info(f"Refund transaction {new_transaction['TransactionID']['S']} created successfully.")
        return new_transaction
    except ClientError as e:
        logger.error(f"DynamoDB put_item failed while creating refund transaction: {e.response['Error']['Message']}")
        raise e

def create_audit_trail(transaction, refund_transaction, user, reason):
    """Create an audit trail entry in DynamoDB for the refund transaction."""
    try:
        audit_entry = {
            'AuditID': {'S': f"{refund_transaction['TransactionID']['S']}-AUDIT"},
            'OriginalTransactionID': {'S': transaction['TransactionID']['S']},
            'RefundTransactionID': {'S': refund_transaction['TransactionID']['S']},
            'Amount': {'N': str(refund_transaction['Amount']['N'])},
            'Reason': {'S': reason},
            'User': {'S': user},
            'Timestamp': {'S': time.strftime('%Y-%m-%dT%H:%M:%SZ')},  # Current time in UTC
        }

        dynamodb.put_item(
            TableName=AUDIT_TRAIL_TABLE,
            Item=audit_entry
        )
        logger.info(f"Audit trail created for refund transaction {refund_transaction['TransactionID']['S']}.")
    except ClientError as e:
        logger.error(f"DynamoDB put_item failed for audit trail entry: {e.response['Error']['Message']}")
        raise e

def send_to_fifo_queue(refund_transaction, user_id):
    """Send the refund transaction details to a FIFO queue."""
    try:
        message = {
            'TransactionID': refund_transaction['TransactionID']['S'],
            'Amount': refund_transaction['Amount']['N'],
            'Reason': refund_transaction['Reason']['S'],
        }

        message_group_id = f"refund-transaction-{user_id}"

        response = sqs.send_message(
            QueueUrl=FIFO_QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageGroupId=message_group_id,
            MessageDeduplicationId=refund_transaction['TransactionID']['S'],
        )
        logger.info(f"Sent refund transaction {refund_transaction['TransactionID']['S']} to FIFO queue.")
    except ClientError as e:
        logger.error(f"SQS send_message failed: {e.response['Error']['Message']}")
        raise e

def lambda_handler(event, context):
    try:
        transaction_id = event.get('transactionId')
        user_id = event.get('userId')
        reason = event.get('reason')

        if not transaction_id or not user_id or not reason:
            logger.error("Missing required input parameters.")
            return {"statusCode": 400, "body": {"error": "Missing required parameters (transactionId, userId, reason)"}}

        transaction = get_transaction(transaction_id)
        if not transaction:
            return {"statusCode": 404, "body": {"error": f"Transaction {transaction_id} not found"}}

        # Validate if the transaction is eligible for voiding or refunding
        validate_transaction(transaction)

        # If the transaction is PAYMENT-SUCCESS, we will process a refund instead of voiding
        status = transaction.get('status', {}).get('S')
        if status == 'PAYMENT-SUCCESS':
            refund_amount = event.get('refundAmount', 100.0)  # Default to 100.0 if not provided
            refund_transaction = create_refund_transaction(transaction, refund_amount, reason)
            create_audit_trail(transaction, refund_transaction, user_id, reason)
            send_to_fifo_queue(refund_transaction, user_id)

            return {"statusCode": 200, "body": {"message": "Refund processed successfully for transaction " + transaction_id}}

        # If voiding is allowed (for other statuses), proceed with void processing
        void_amount = event.get('voidAmount', 100.0)  # Default to 100.0 if not provided
        void_transaction = revert_transaction(transaction, void_amount, reason)
        create_audit_trail(transaction, void_transaction, user_id, reason)
        send_to_fifo_queue(void_transaction, user_id)

        return {"statusCode": 200, "body": {"message": "Void processed successfully for transaction " + transaction_id}}

    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return {"statusCode": 400, "body": {"error": str(ve)}}
    except ClientError as ce:
        logger.error(f"AWS Client error: {str(ce)}")
        return {"statusCode": 500, "body": {"error": str(ce)}}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"statusCode": 500, "body": {"error": f"Internal server error: {str(e)}"}}
