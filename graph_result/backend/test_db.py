from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

driver = GraphDatabase.driver(URI, auth=AUTH)

queries = [
    "MATCH (c:Customer) RETURN c LIMIT 2",
    "MATCH (s:SalesOrder) RETURN s LIMIT 2"
]

with driver.session() as session:
    for q in queries:
        print(f"QUERY: {q}")
        res = session.run(q)
        for r in res:
            print(r.data())
driver.close()
