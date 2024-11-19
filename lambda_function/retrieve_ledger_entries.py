# DynamoDB Query: Query the TransactionsTable by transaction ID.
# Validation Logic: Check the status and conditions for eligibility.

import boto3
import logging
import json
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = "TransactionsTable"  # Replace with your actual table name
table = dynamodb.Table(table_name)

# Initialize Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to handle retrieving and reverting ledger entries for a void transaction.
    """
    try:
        # Step 1: Parse transaction ID from the event
        transaction_id = event.get('transaction_id')
        if not transaction_id:
            return error_response("Transaction ID is required.")
        
        logger.info(f"Processing void for Transaction ID: {transaction_id}")

        # Step 2: Retrieve ledger entries
        ledger_entries = get_ledger_entries(transaction_id)
        if not ledger_entries:
            return error_response(f"No ledger entries found for Transaction ID: {transaction_id}")
        
        # Step 3: Validate entries for void eligibility
        if not is_transaction_eligible(ledger_entries):
            return error_response(f"Transaction ID {transaction_id} is not eligible for voiding.")

        # Step 4: Prepare void entries
        void_entries = prepare_void_entries(ledger_entries, transaction_id)

        # Step 5: Log and return the void entries
        logger.info(f"Void entries prepared for Transaction ID {transaction_id}: {json.dumps(void_entries)}")
        return success_response({"void_entries": void_entries})

    except ClientError as e:
        logger.error(f"ClientError: {str(e)}")
        return error_response("Error interacting with the database.", 500)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return error_response("Internal server error.", 500)


def get_ledger_entries(transaction_id):
    """
    Retrieve ledger entries for the given transaction ID.
    """
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('TransactionID').eq(transaction_id)
        )
        return response.get('Items', [])
    except ClientError as e:
        logger.error(f"Error retrieving ledger entries: {e.response['Error']['Message']}")
        raise


def is_transaction_eligible(ledger_entries):
    """
    Check if a transaction is eligible for voiding.
    """
    for entry in ledger_entries:
        status = entry.get('Status', '')
        if status in ['Refunded', 'Settled', 'Voided']:
            logger.warning(f"Transaction is not eligible for voiding. Current status: {status}")
            return False
    return True


def prepare_void_entries(ledger_entries, transaction_id):
    """
    Prepare void entries for the given transaction.
    """
    void_entries = []
    for entry in ledger_entries:
        void_entry = {
            "TransactionID": transaction_id,
            "OriginalEntryID": entry['EntryID'],
            "Type": "Void",
            "Amount": -entry['Amount'],  # Reverse the amount
            "Timestamp": entry.get('Timestamp', "N/A"),
            "Status": "Voided"
        }
        void_entries.append(void_entry)
    return void_entries


def success_response(data, status_code=200):
    """
    Return a success response.
    """
    return {
        "statusCode": status_code,
        "body": json.dumps({"success": True, "data": data})
    }


def error_response(message, status_code=400):
    """
    Return an error response.
    """
    return {
        "statusCode": status_code,
        "body": json.dumps({"success": False, "error": message})
    }
