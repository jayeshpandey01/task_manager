from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
pwd = os.getenv("NEO4J_PASSWORD", "password")

print(f"Testing connection to {uri} as {user}...")
try:
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    driver.verify_connectivity()
    print(">>> SUCCESS! Connection to Neo4j works.")
    driver.close()
except Exception as e:
    print(f">>> FAILED! {e}")
