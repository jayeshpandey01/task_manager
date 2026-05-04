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
        res = session.run('CALL apoc.help("text") YIELD name RETURN count(*)').single()
        print('APOC text functions count:', res[0])
    except Exception as e:
        print('APOC error:', e)
driver.close()
