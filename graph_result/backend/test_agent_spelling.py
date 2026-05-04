from agent.langgraph_agent import invoke_agent

test_query = "Which customers ordered the almondd and tsyme berdd oilll?"
print(f"Testing BAD SPELLING query: {test_query}")

result = invoke_agent(test_query)

print("Generated Cypher Query:")
print(result.get("cypher_query", "No Cypher generated"))
print("Error:", result.get("error"))

res_list = result.get('results')
print(f"\nFound {len(res_list) if res_list else 0} matches")
