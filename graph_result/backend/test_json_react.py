import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, format="json", timeout=120)

sys_prompt = """You are a graph database agent.
You MUST output ONLY valid JSON.
Tools available:
- search_customer (arg: customer name)
- search_product (arg: product name)
- get_customer_orders (arg: customer ID)
- get_order_details (arg: order ID)
- FINAL_ANSWER (arg: your final answer to the user)

If you need to use a tool, output:
{"thought": "reasoning...", "tool": "tool_name", "arg": "argument"}
"""

messages = [
    SystemMessage(content=sys_prompt),
    HumanMessage(content="Question: Show me the delivery status of everything ordered by the Melton Group.")
]

res = llm.invoke(messages)
print("Turn 1:", res.content)

messages.append(res)
messages.append(HumanMessage(content='Tool Result: [{"id": "320000108", "name": "Melton Group"}]'))

res2 = llm.invoke(messages)
print("Turn 2:", res2.content)

messages.append(res2)
messages.append(HumanMessage(content='Tool Result: [{"order_id": "740596", "status": "Open"}]'))

res3 = llm.invoke(messages)
print("Turn 3:", res3.content)
