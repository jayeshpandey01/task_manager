from neo4j import GraphDatabase
import traceback

uri_guesses = [
    "neo4j+s://7506fb47.databases.neo4j.io",
    "bolt://7506fb47.databases.neo4j.io:7687",
    "bolt://localhost:7687"
]
user_guesses = ["neo4j", "7506fb47"]
pwd = "OA1IGxZCVx9bvM8fe1ccP71Wy1cm3n_B8tS4jjyd-OQ"

success = False
for uri in uri_guesses:
    for user in user_guesses:
        print(f"Trying URI: {uri} | User: {user}")
        try:
            driver = GraphDatabase.driver(uri, auth=(user, pwd))
            driver.verify_connectivity()
            print(">>> SUCCESS! Connection to Neo4j works.")
            print(f"URI: {uri}")
            print(f"USER: {user}")
            driver.close()
            success = True
            break
        except Exception as e:
            print("Failed:", str(e).splitlines()[0])
    if success:
        break

if not success:
    print("Could not connect with any combination.")
