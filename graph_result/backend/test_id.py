from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

driver = GraphDatabase.driver(URI, auth=AUTH)

with driver.session() as session:
    res = session.run("MATCH (n:Customer) RETURN n.id LIMIT 10")
    print("Sample Customer IDs:")
    for r in res:
        print(f"- {r[0]}")
    
    res = session.run("MATCH (n:Customer) WHERE n.id CONTAINS 'BP' RETURN n.id LIMIT 5")
    print("\nCustomer IDs containing 'BP':")
    for r in res:
        print(f"- {r[0]}")

driver.close()
