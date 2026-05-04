from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
pwd = os.getenv("NEO4J_PASSWORD", "password")

try:
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
        print("Database Node Stats:")
        for record in result:
            print(f"- {record['labels']}: {record['count']}")
    driver.close()
except Exception as e:
    print(f">>> FAILED! {e}")
