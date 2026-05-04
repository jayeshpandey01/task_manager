import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
import requests

load_dotenv(dotenv_path="backend/.env")

# Test queries to verify "fuzzy" matching
TEST_QUERIES = [
    "high-grade steel parts",  # Matches Product P01 description
    "vip customers",           # Matches 'Platinum' category
    "global logistics"         # Matches Customer name
]

def get_embedding(text):
    url = f"{os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/embeddings"
    model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    try:
        res = requests.post(url, json={"model": model, "prompt": text}, timeout=10)
        res.raise_for_status()
        return res.json().get("embedding")
    except Exception as e:
        print(f"❌ Error getting embedding for '{text}': {e}")
        return None

def test_search():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
    
    try:
        driver = GraphDatabase.driver(uri, auth=auth)
        with driver.session() as session:
            for q in TEST_QUERIES:
                print(f"\n🔍 Testing query: '{q}'")
                vec = get_embedding(q)
                if not vec:
                    continue

                # 1. Product Match Check
                print("--- Checking Products ---")
                res_prod = session.run(
                    "CALL db.index.vector.queryNodes('product_description_vector', 1, $v) YIELD node, score RETURN node.id as id, node.description as desc, score",
                    v=vec
                )
                for r in res_prod:
                    print(f"✅ Product: {r['id']} | Score: {r['score']:.4f} | Desc: {r['desc'][:50]}...")

                # 2. Customer Category Match Check
                print("--- Checking Categories ---")
                res_cat = session.run(
                    "CALL db.index.vector.queryNodes('customer_category_vector', 1, $v) YIELD node, score RETURN node.id as id, node.category as cat, score",
                    v=vec
                )
                for r in res_cat:
                    print(f"✅ Category Match for Customer {r['id']} | Score: {r['score']:.4f} | Category: {r['cat']}")

        driver.close()
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_search()
