from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
pwd = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    result = session.run("MATCH (n)-[r]->(m) RETURN r LIMIT 1")
    record = result.single()
    if record:
        rel = record["r"]
        print(f"Rel type: {rel.type}")
        print(f"Start node ID (internal): {rel.start_node}")
        # Try to access properties if it's a node proxy
        try:
            print(f"Start node 'id' prop: {rel.start_node['id']}")
        except Exception as e:
            print(f"Could not access start_node properties directly: {e}")
            
        print(f"Nodes in rel: {rel.nodes}")
driver.close()
