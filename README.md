# Process-Void: Retrieving, Persisting Ledger, and Audit Trail

## 1. Retrieving Ledger Entries to Revert

### **Objective:**

Retrieve ledger entries (e.g., payment transactions) that need to be voided or reverted.

### **Steps:**

1. **Identify Target Entries:**
   - Use the unique transaction ID, payment reference, or order ID from the void request payload.
   - Query DynamoDB (or the ledger database) to retrieve the relevant ledger entry.

2. **Validate Entry Status:**
   - Ensure the entry is eligible for voiding (e.g., check its status like "Pending" or "Authorized").
   - Avoid voiding completed or already voided transactions.

3. **Prepare for Reversion:**
   - Extract necessary fields like transaction amount, payment processor details, and void reason.

### **Terraform Implementation:**

- Create a Lambda function with:
  - **DynamoDB Query:** Query the TransactionsTable by transaction ID.
  - **Validation Logic:** Check the status and conditions for eligibility.

---

## 2. Persisting Payment Ledger

### **Objective:**

Update or insert entries in the payment ledger (DynamoDB or equivalent database) to reflect the void operation.

### **Steps:**

1. **Insert Void Record:**
   - Add a new entry for the void transaction with details:
     - `transactionId` (original)
     - `voidTransactionId` (unique ID for void operation)
     - `status`: "Voided"
     - `voidReason`: "User Requested", "System Error", etc.
     - `timestamp`: Current date and time.

2. **Mark Original Transaction:**
   - Update the original ledger entry to reflect the void operation:
     - `status`: "Voided"
     - `linkedTransactionId`: (reference to the voidTransactionId).

3. **Log Additional Metadata:**
   - Include fields for reconciliation, such as processor response codes or external references.

### **Terraform Implementation:**

- Create a Lambda function that:
  - Inserts the void transaction as a new item in the TransactionsTable.
  - Updates the original transaction entry with void-related fields.

---

## 3. Persisting Payment Audit Trail

### **Objective:**

Maintain a record of every action taken during the void process for traceability and compliance.

### **Steps:**

1. **Track Action Details:**
   - Record who initiated the void, when, and why.
   - Include the transaction ID and linked void transaction ID.

2. **Log Every Interaction:**
   - Log system checks, validations, database queries, and external API calls made during the void process.

3. **Store Metadata:**
   - Save details like:
     - `actor`: User, system, or process that triggered the void.
     - `action`: "Void Initiated," "Void Completed," etc.
     - `details`: Include processor responses, timestamps, and success/failure statuses.

4. **Ensure Ordered Persistence:**
   - Use SQS FIFO Messaging to persist audit logs in order if required.

### **Terraform Implementation:**

- Create a Lambda function that:
  - Inserts audit trail records into the AuditTrailTable in DynamoDB.
  - Optionally uses an SQS FIFO queue to handle ordered processing.
  - Includes IAM permissions for DynamoDB writes and SQS operations.

---

## Clear Understanding

### **Ledger Entries:**

The payment ledger is the authoritative record of all transactions. When voiding, you retrieve entries to validate eligibility, revert changes, and log results.

### **Payment Ledger:**

The ledger updates ensure that all related transactions, including voids, are recorded with complete traceability.

### **Payment Audit Trail:**

The audit trail is for compliance and debugging. It records who accessed what, when, and why during the void process, including system actions like validations and updates.

---

## Data Flow

1. **Input:** Void request payload.
2. **Retrieve:** Query TransactionsTable to get the original transaction.
3. **Process:** Update TransactionsTable with the void status and create a void record.
4. **Audit:** Log actions in the AuditTrailTable for monitoring.
