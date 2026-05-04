from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, timeout=120, num_ctx=4096)

prompt = PromptTemplate.from_template(
    "You are a reasoning database agent navigating an Order-to-Cash graph.\n"
    "You must search for information step-by-step using tools.\n"
    "TOOLS AVAILABLE:\n"
    "- search_customer: <name> (Finds customer ID)\n"
    "- get_customer_orders: <customer_id> (Gets orders for a customer)\n"
    "- search_product: <name> (Finds product ID)\n"
    "- END: <answer> (Provide the final answer when you have enough data)\n\n"
    "Current Context:\n{context}\n\n"
    "User Question: {question}\n\n"
    "What tool do you call next to solve the question? Reply in EXACTLY this format: 'CALL tool: arg'. No other text."
)

ctx = "- User asks about 'melton group'."
print("TEST 1:")
res1 = llm.invoke(prompt.format(context=ctx, question="Find orders for the melton group"))
print("A:", res1.content)

ctx += "\n- Called search_customer: melton group -> Result: ID 320000108"
print("\nTEST 2:")
res2 = llm.invoke(prompt.format(context=ctx, question="Find orders for the melton group"))
print("A:", res2.content)

ctx += "\n- Called get_customer_orders: 320000108 -> Result: Orders 740596, 740597"
print("\nTEST 3:")
res3 = llm.invoke(prompt.format(context=ctx, question="Find orders for the melton group"))
print("A:", res3.content)
