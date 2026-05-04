from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))
with driver.session() as session:
    result = session.run("MATCH (o:SalesOrder {id: '740506'})-[:HAS_ITEM]->(i:SalesOrderItem) RETURN o, count(i) as items")
    record = result.single()
    if record:
        print(f"Order 740506 exists with {record['items']} items.")
    else:
        print("Order 740506 was NOT found.")
driver.close()
