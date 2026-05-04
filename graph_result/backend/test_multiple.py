from agent.langgraph_agent import invoke_agent
queries = [
    "What is the status of sales order 740506?",
    "Show me orders for customer 310000108",
    "Which customers ordered the facewash vit c?"
]
for q in queries:
    print(f"QUERY: {q}")
    res = invoke_agent(q)
    print(f"CYPHER: {res.get('cypher_query')}")
    print(f"RECORDS: {len(res.get('results', []))}")
    print("-" * 50)
