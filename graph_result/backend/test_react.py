from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate

@tool
def search_customer(name: str) -> str:
    """Searches for a customer by name and returns their ID."""
    if "melton" in name.lower():
        return "Customer ID is 320000108"
    return "Not found"

@tool
def get_orders(customer_id: str) -> str:
    """Gets orders for a customer ID."""
    if customer_id == "320000108":
        return "Orders are 740596, 740597"
    return "No orders"

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0)
tools = [search_customer, get_orders]

prompt = PromptTemplate.from_template(
    "You are an agent. Use the tools to answer the question.\n"
    "Tools:\n{tools}\n\n"
    "Use the following format:\n"
    "Question: the input question\n"
    "Thought: what to do next\n"
    "Action: the action to take, should be one of [{tool_names}]\n"
    "Action Input: the input to the action\n"
    "Observation: the result\n"
    "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
    "Thought: I know the final answer\n"
    "Final Answer: the final answer\n\n"
    "Question: {input}\n"
    "Thought:{agent_scratchpad}"
)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3)

try:
    res = agent_executor.invoke({"input": "Find the orders for the melton group"})
    print("RES:", res)
except Exception as e:
    print("FAILED:", e)
