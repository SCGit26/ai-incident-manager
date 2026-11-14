# AI-Driven Procure-to-Pay (PTP) Incident Manager

An automated, Generative AI-powered Incident Manager triage pipeline designed to ingest unstructured Procure-to-Pay (PTP) support tickets from a PostgreSQL database, classify and prioritize bottlenecks using Google Gemini with schema validation, and export executive-ready SLA reports.

---

## Business Problem & Value Proposition
In enterprise Procure-to-Pay operations, Tier-1 support queues are frequently bottlenecked by unstructured, high-volume incident tickets ranging from vendor portal lockouts to 3-way GR/IR matching errors and EDI transmission failures. Manual triage delays SLA resolution and obscures systemic ERP blockers.

This solution automates the front-line triage workflow by:
* **Eliminating Manual Classification:** Uses LLM reasoning to categorize raw user descriptions into standardized PTP operational domains.
* **Enforcing Data Integrity:** Leverages structured JSON outputs rather than brittle string parsing to guarantee deterministic pipeline stability.
* **Prioritizing Operational Blockers:** Automatically ranks incidents by urgency (`Critical` to `Low`) and generates actionable technical troubleshooting steps.
* **Enabling Flexible Execution:** Supports scheduled background automation via Windows Task Scheduler.

---

## System Architecture & Tech Stack

```
[PostgreSQL Database] ──(psycopg2 / SQL)──> [Python ETL & Batcher]
                                                    │
                                       (Structured JSON Payload)
                                                    ▼
[Executive SLA Report (.csv)] <──(Pandas)── [Google Gemini API]
                                            (gemini-3.5-flash-lite + Pydantic)
```

* **Database:** PostgreSQL (`ap.itsm_incidents` schema storing raw unstructured ticket logs and department metadata).
* **Core Language:** Python
* **Generative AI & Validation:** `google-genai` SDK (`gemini-3.5-flash-lite`) paired with `pydantic` for strict schema enforcement.
* **Data Manipulation:** `pandas` and `psycopg2-binary` for database extraction, priority sorting, and CSV report formatting.
* **Orchestration:** Windows Task Scheduler for recurring daily batch runs.

---

## Key Engineering Features
1. **Batch Processing Optimization:** Aggregates open tickets into a single structured payload per run, minimizing API latency.
2. **Deterministic Schema Validation:** Defines a strict `BatchTriageResponse` Pydantic model (`ticket_id`, `category`, `priority`, `suggested_action`) to ensure zero malformed outputs enter downstream reporting.
3. **Executive Report Formatting:** Automatically sorts tickets by severity rank (`Critical` → `High` → `Medium` → `Low`), reorders columns for rapid scanning, and outputs clean, human-readable headers to `incident_sla_report.csv`.
4. **Zero-Hardcoded Secrets:** Retrieves `GEMINI_API_KEY` and `PGPASSWORD` securely from OS-level environment variables.

---

## Setup & Installation

### 1. Prerequisites
* A free API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Database Setup
Execute the SQL scripts in sequential order inside your target PostgreSQL database to build the table and load the test dataset.

```sql
-- Step 1: Create the ap.itsm_incidents table
\i sql/01_create_table.sql

-- Step 2: Populate test dataset
\i sql/02_support_ticket_data.sql
```

### 3. Install Python Dependencies
Install the required Python packages in your local Python environment:
```bash
pip install google-genai pydantic psycopg2-binary pandas
```

### 4. Configure Environment Variables
Set the following environment variables in your operating system (e.g., Windows System Environment Variables) so both terminal sessions and background scheduled tasks can authenticate securely:
* `GEMINI_API_KEY`: Your Google AI Studio API key
* `PGPASSWORD`: Your PostgreSQL database password

---

### Optional Scheduled Automation (Windows Task Scheduler)
To run the agent automatically (e.g., daily at 8:00 AM):
1. Open **Windows Task Scheduler** and select **Create Basic Task**.
2. Set the trigger to **Daily** at your desired execution time.
3. Set the action to **Start a program**:
   * **Program/script:** Path to your `python.exe` executable.
   * **Add arguments:** `ai_triage_agent.py`
   * **Start in:** Full path to your project folder (e.g., `C:\Users\<user>\Desktop\ptp-projects\incident-manager`).

---

## Sample Output (`incident_sla_report.csv`)

| Ticket ID | Priority Level | Category | Department | Suggested Resolution Action | Raw Ticket Text |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **INC-1003** | Critical | Workflow Error | Accounts Payable | Inspect ERP workflow routing rules for null approver IDs and re-trigger approval batch job. | *"Urgent: All invoices over $10k are stuck in pending status and not routing to directors."* |
| **INC-1001** | High | Vendor Portal Access | Procurement | Verify vendor IAM account status in supplier portal and trigger an automated password reset token. | *"Supplier Acme Corp says they are locked out of the portal and cannot submit their Q3 invoice."* |
| **INC-1002** | High | GR/IR Matching Block | Supply Chain | Compare Goods Receipt quantity against Purchase Order line item 20 and clear tolerance variance block. | *"Invoice #88492 is blocked for payment due to a 3-way match quantity discrepancy on PO 450012."* |