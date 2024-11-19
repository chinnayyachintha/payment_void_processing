# Inserts the void transaction as a new item in the TransactionsTable.
# Updates the original transaction entry with void-related fields.

import boto3
import logging
import os
import uuid
import time

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("TRANSACTIONS_TABLE")  # Table name from environment variable
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    try:
        # Step 1: Validate input
        original_transaction_id = event.get("transactionId")
        void_reason = event.get("voidReason", "Not Specified")

        if not original_transaction_id:
            logger.error("Missing required parameter: transactionId")
            return {
                "statusCode": 400,
                "body": {"error": "transactionId is required"}
            }

        # Step 2: Generate unique void transaction ID
        void_transaction_id = str(uuid.uuid4())
        timestamp = int(time.time())

        # Step 3: Check if the original transaction exists
        response = table.get_item(Key={"TransactionID": original_transaction_id})
        original_transaction = response.get("Item")

        if not original_transaction:
            logger.error(f"Original transaction not found: {original_transaction_id}")
            return {
                "statusCode": 404,
                "body": {"error": f"Transaction {original_transaction_id} not found"}
            }

        # Step 4: Check if the transaction is already voided or refunded
        if original_transaction.get("Status") in ["Voided", "Refunded"]:
            logger.warning(f"Transaction {original_transaction_id} is not eligible for void")
            return {
                "statusCode": 400,
                "body": {"error": f"Transaction {original_transaction_id} cannot be voided"}
            }

        # Step 5: Insert void transaction entry
        void_entry = {
            "TransactionID": void_transaction_id,
            "Status": "Voided",
            "VoidReason": void_reason,
            "LinkedTransactionID": original_transaction_id,
            "Timestamp": timestamp
        }
        table.put_item(Item=void_entry)
        logger.info(f"Void transaction recorded: {void_entry}")

        # Step 6: Update original transaction status
        table.update_item(
            Key={"TransactionID": original_transaction_id},
            UpdateExpression="SET #s = :status, LinkedTransactionID = :void_id",
            ExpressionAttributeNames={"#s": "Status"},
            ExpressionAttributeValues={
                ":status": "Voided",
                ":void_id": void_transaction_id
            }
        )
        logger.info(f"Original transaction updated: {original_transaction_id}")

        # Step 7: Return success response
        return {
            "statusCode": 200,
            "body": {
                "message": "Void transaction processed successfully",
                "voidTransactionID": void_transaction_id,
                "originalTransactionID": original_transaction_id
            }
        }

    except Exception as e:
        logger.error(f"Error processing void transaction: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": "Internal server error"}
        }
