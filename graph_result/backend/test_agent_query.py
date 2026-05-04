from agent.langgraph_agent import invoke_agent
import os
from dotenv import load_dotenv

load_dotenv()

# Test a query that should definitely work based on the sample data I saw in create_sample_data.py
test_query = '\"Which customers ordered the almond and thyme beard oil?\"'
print(f"Testing query: {test_query}")

result = invoke_agent(test_query)

print("\n--- Agent Result ---")
print(f"Intent: {result.get('intent')}")
print(f"Cypher: {result.get('cypher_query')}")
print(f"Response: {result.get('response')}")
print(f"Results Count: {len(result.get('results', []))}")
if result.get('error'):
    print(f"Error: {result.get('error')}")
