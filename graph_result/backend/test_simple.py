from agent.langgraph_agent import invoke_agent

res = invoke_agent("What is the delivery status of order 740506?")
print("CYPHER QUERY:")
print(res.get("cypher_query"))
print("\nFINAL RESPONSE:")
print(res.get("response"))
