from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def create_sample_data():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            # Clear old data
            print("Clearing old data...")
            session.run("MATCH (n) DETACH DELETE n")
            
            # Create full O2C graph
            print("Creating complete Order-to-Cash data graph...")
            session.run("""
            // 1. Geography
            CREATE (a1:Address {id: 'ADDR1', cityName: 'New York', streetName: '5th Ave', country: 'US'})

            // 2. Organization Unit
            CREATE (p1:Plant {id: '1920', name: 'Main Warehouse', salesOrganization: 'US01'})-[:HAS_ADDRESS]->(a1)

            // 3. Customer & Master Data
            CREATE (c1:Customer {id: '310000108', name: 'Global Logistics', category: 'Platinum'})-[:HAS_ADDRESS]->(a1)
            CREATE (prod:Product {id: 'P01', name: 'Industrial Metal Parts', description: 'High-grade steel components for manufacturing'})

            // 4. Sales Order Flow
            CREATE (o1:SalesOrder {id: '5000000021', creationDate: '2026-03-29', totalNetAmount: 1500, overallDeliveryStatus: 'C', transactionCurrency: 'USD'})
            CREATE (c1)-[:PLACED]->(o1)

            CREATE (oi1:SalesOrderItem {id: '5000000021_10', itemNumber: '10', netAmount: 1500})
            CREATE (o1)-[:HAS_ITEM]->(oi1)
            CREATE (oi1)-[:IS_PRODUCT]->(prod)
            CREATE (oi1)-[:SHIPPED_FROM]->(p1)

            // 5. Delivery Flow
            CREATE (d1:OutboundDelivery {id: '80000001', creationDate: '2026-03-29', overallGoodsMovementStatus: 'C'})
            CREATE (di1:OutboundDeliveryItem {id: '80000001_10', actualDeliveryQuantity: 10})
            CREATE (d1)-[:HAS_ITEM]->(di1)
            CREATE (di1)-[:FULFILLS]->(oi1)
            CREATE (di1)-[:SHIPPED_FROM]->(p1)

            // 6. Billing & Payment
            CREATE (b1:BillingDocument {id: '90000005', billingDocumentDate: '2026-03-29', totalNetAmount: 1500})
            CREATE (bi1:BillingDocumentItem {id: '90000005_10', netAmount: 1500})
            CREATE (b1)-[:HAS_ITEM]->(bi1)
            CREATE (bi1)-[:BILLS_FOR]->(di1)
            CREATE (b1)-[:BILLED_TO]->(c1)

            CREATE (acc1:AccountingDocument {id: '1000001', amountInTransactionCurrency: 1500, status: 'Cleared'})
            CREATE (b1)-[:HAS_ACCOUNTING_DOC]->(acc1)
            CREATE (c1)-[:PAID]->(acc1)
            """)
            print("✅ COMPLETE O2C DATA CREATED SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ Error during sample data creation: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    create_sample_data()
