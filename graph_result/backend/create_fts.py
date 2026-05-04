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
        session.run("CREATE FULLTEXT INDEX product_fts IF NOT EXISTS FOR (n:Product) ON EACH [n.description]")
        print("Successfully created 'product_fts' Fulltext Index for robust fuzzy searching.")
    except Exception as e:
        print("Failed to create index:", e)
driver.close()
