import json
from agent.langgraph_agent import invoke_agent

test_query = "Which customers ordered the almond and thyme beard oil?"
result = invoke_agent(test_query)
with open("agent_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
