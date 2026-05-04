from neo4j import GraphDatabase
import os
import json
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
pwd = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    with open("actual_data_utf8.txt", "w", encoding="utf-8") as f:
        f.write("--- CUSTOMERS ---\n")
        for r in session.run("MATCH (c:Customer) RETURN c LIMIT 3"): f.write(json.dumps(dict(r['c'])) + "\n")
        f.write("--- MATERIALS ---\n")
        for r in session.run("MATCH (m:Material) RETURN m LIMIT 3"): f.write(json.dumps(dict(r['m'])) + "\n")
        f.write("--- SALES ORDERS ---\n")
        for r in session.run("MATCH (s:SalesOrder) RETURN s LIMIT 5"): f.write(json.dumps(dict(r['s'])) + "\n")
        f.write("--- SALES ORDER ITEMS ---\n")
        for r in session.run("MATCH (i:SalesOrderItem) RETURN i LIMIT 3"): f.write(json.dumps(dict(r['i'])) + "\n")
driver.close()
