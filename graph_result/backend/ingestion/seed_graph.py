import os
import json
from neo4j import GraphDatabase
import glob
from queries import (
    CREATE_CONSTRAINTS, MERGE_CUSTOMER, MERGE_PRODUCT, MERGE_SALES_ORDER,
    MERGE_SALES_ORDER_ITEM, MERGE_OUTBOUND_DELIVERY, MERGE_OUTBOUND_DELIVERY_ITEM,
    MERGE_BILLING_DOCUMENT, MERGE_BILLING_DOCUMENT_ITEM, MERGE_PAYMENT,
    MERGE_ADDRESS, MERGE_PRODUCT_DESCRIPTION, MERGE_PLANT, MERGE_PRODUCT_PLANT,
    MERGE_PRODUCT_STORAGE_LOCATION, MERGE_SALES_ORDER_SCHEDULE_LINE
)
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")) # Use generic default password, recommend user changes this.

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sap-o2c-data'))

def load_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return data

def ingest_directory(directory_name, query, driver, batch_size=1000):
    dir_path = os.path.join(DATA_DIR, directory_name)
    if not os.path.exists(dir_path):
        print(f"Directory {dir_path} not found. Skipping.")
        return
    
    files = glob.glob(os.path.join(dir_path, "*.jsonl"))
    for file_path in files:
        data = load_jsonl(file_path)
        if not data:
            continue
        
        # Batch insert
        with driver.session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                try:
                    session.run(query, batch=batch)
                    print(f"Ingested {len(batch)} records from {directory_name} ({file_path})")
                except Exception as e:
                    print(f"Error ingesting batch from {file_path}: {e}")

def main():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    print("Creating constraints...")
    with driver.session() as session:
        for constraint in CREATE_CONSTRAINTS:
            try:
                session.run(constraint)
            except Exception as e:
                print(f"Constraint creation error (might already exist): {e}")

    print("Clearing old dummy data...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # The order is important for node merging and relationships
    ingestion_steps = [
        ("business_partner_addresses", MERGE_ADDRESS),
        ("business_partners", MERGE_CUSTOMER),
        ("plants", MERGE_PLANT),
        ("products", MERGE_PRODUCT),
        ("product_descriptions", MERGE_PRODUCT_DESCRIPTION),
        ("product_plants", MERGE_PRODUCT_PLANT),
        ("product_storage_locations", MERGE_PRODUCT_STORAGE_LOCATION),
        ("sales_order_headers", MERGE_SALES_ORDER),
        ("sales_order_items", MERGE_SALES_ORDER_ITEM),
        ("sales_order_schedule_lines", MERGE_SALES_ORDER_SCHEDULE_LINE),
        ("outbound_delivery_headers", MERGE_OUTBOUND_DELIVERY),
        ("outbound_delivery_items", MERGE_OUTBOUND_DELIVERY_ITEM),
        ("billing_document_headers", MERGE_BILLING_DOCUMENT),
        ("billing_document_items", MERGE_BILLING_DOCUMENT_ITEM),
        ("payments_accounts_receivable", MERGE_PAYMENT)
    ]

    for dir_name, query in ingestion_steps:
        print(f"Starting ingestion for {dir_name}...")
        ingest_directory(dir_name, query, driver)

    print("Data ingestion complete.")
    driver.close()

if __name__ == "__main__":
    main()
