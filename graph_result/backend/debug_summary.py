from agent.langgraph_agent import llm
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# Simulate a table from the screenshot
table_text = """
SALESORDER_SALESORDERTYPE | SALESORDER_TRANSACTIONCURRENCY | SALESORDER_OVERALLDELIVERYSTATUS | SALESORDER_TOTALNETAMOUNT | SALESORDER_ID | SALESORDER_CREATIONDATE
OR | INR | C | 17108.25 | 740506 | 2025-03-31T00:00:00.000Z
"""

question = "Give me a summary of order 740506"

prompt = PromptTemplate.from_template(
    "You are an expert analyzing Order-to-Cash (O2C) business data.\n"
    "The table below is the ONLY verified source of truth from the Neo4j database.\n"
    "Note: Column names are prefixed with node labels (e.g., SalesOrder_id, Product_description).\n"
    "RULES:\n"
    "- Answer SOLELY based on values in the table.\n"
    "- Reference specific IDs, statuses, or dates from the table.\n"
    "- If table is empty, say 'No matching records found.'\n"
    "- Be concise.\n\n"
    "Verified Data Table:\n"
    "{table_text}\n\n"
    "User Question: {question}\n"
    "Response:"
)

chain = prompt | llm

print("Sending to Ollama...")
try:
    res = chain.invoke({"question": question, "table_text": table_text})
    print("--- SUCCESS ---")
    print(res.content)
except Exception as e:
    print("--- FAILED ---")
    print(f"Error type: {type(e)}")
    print(f"Error: {e}")
