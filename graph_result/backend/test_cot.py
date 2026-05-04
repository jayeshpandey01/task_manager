from agent.langgraph_agent import invoke_agent

res = invoke_agent("Which customers ordered the facewash vit c?")
print("CYPHER QUERY:")
print(res.get("cypher_query"))
print("\nFINAL RESPONSE:")
print(res.get("response"))
