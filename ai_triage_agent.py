import os
import json
import psycopg2
import pandas as pd
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Verify API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing! Run: set GEMINI_API_KEY=your_key_here")

client = genai.Client(api_key=api_key)

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "procurement_analytics",
    "user": "postgres",
    "password": os.getenv("PGPASSWORD", "")
}

class TicketClassification(BaseModel):
    ticket_id: str
    category: str = Field(description="Category e.g. Vendor Portal Access, GR/IR Matching Block, Workflow Error, EDI Transmission, Tax Reconciliation")
    priority: str = Field(description="Low, Medium, High, or Critical")
    suggested_action: str = Field(description="Specific technical troubleshooting step for the IT analyst")

class BatchTriageResponse(BaseModel):
    results: list[TicketClassification]

def run():
    print("--- Starting AI-Driven ITSM Triage Pipeline ---")
    
    # 1. Pull raw tickets from PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql_query("SELECT ticket_id, user_department, raw_ticket_text FROM ap.itsm_incidents;", conn)
    conn.close()
    print(f"[INFO] Loaded {len(df)} tickets from database.")

    # 2. Send batch to Gemini
    tickets_payload = df[["ticket_id", "user_department", "raw_ticket_text"]].to_dict(orient="records")
    
    prompt = f"""
    You are an expert Enterprise Procure-to-Pay (PTP) and ITSM Support Agent.
    Classify every support ticket in the list below. Assign an accurate PTP category, 
    a realistic priority level, and a concrete technical resolution step.

    Tickets:
    {json.dumps(tickets_payload, indent=2)}
    """

    print("[INFO] Sending batch to Gemini for structured classification...")
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=BatchTriageResponse,
        ),
    )

    # 3. Parse JSON and merge back into DataFrame
    parsed = json.loads(response.text)
    ai_df = pd.DataFrame(parsed["results"])
    final_df = pd.merge(df, ai_df, on="ticket_id", how="left")

    # 4. Format and Structure for Readability
    # Sort by priority order (Critical -> High -> Medium -> Low)
    priority_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    final_df["priority_rank"] = final_df["priority"].map(priority_order).fillna(5)
    final_df = final_df.sort_values("priority_rank").drop(columns=["priority_rank"])

    # Reorder columns logically
    final_df = final_df[[
        "ticket_id", 
        "priority", 
        "category", 
        "user_department", 
        "suggested_action", 
        "raw_ticket_text"
    ]]

    # Clean, professional column headers
    final_df.columns = [
        "Ticket ID", 
        "Priority Level", 
        "Category", 
        "Department", 
        "Suggested Resolution Action", 
        "Raw Ticket Text"
    ]

    # 5. Export to CSV
    final_df.to_csv("incident_sla_report.csv", index=False)
    print("\n--- AI Triage Complete ---")
    print("Report successfully formatted and exported to 'incident_sla_report.csv'.\n")
    
    # Print clean preview to console
    print(final_df[["Ticket ID", "Priority Level", "Category", "Department"]].to_string(index=False))

if __name__ == "__main__":
    run()