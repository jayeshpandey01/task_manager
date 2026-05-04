from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
pwd = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    try:
        session.run("CREATE FULLTEXT INDEX customer_fts IF NOT EXISTS FOR (n:Customer) ON EACH [n.name, n.category]")
        print("Successfully created 'customer_fts' Fulltext Index.")
    except Exception as e:
        print("Failed to create customer_fts:", e)
driver.close()
