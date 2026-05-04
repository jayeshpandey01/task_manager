from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
pwd = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    query = "CALL db.index.fulltext.queryNodes('product_fts', 'almondd~ AND yhme~') YIELD node AS p RETURN p"
    res = session.run(query).data()
    print('FTS matches:', len(res))
driver.close()
