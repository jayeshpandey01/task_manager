import os
import re
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# State Definition
class GraphState(TypedDict, total=False):
    question: str
    intent: Optional[str]
    history: List[str]          # Action/Observation loop
    query_results: List[dict]   # Accumulated Neo4j Records for the Graph UI
    table_data: List[dict]
    table_columns: List[str]
    final_response: Optional[str]
    error: Optional[str]
    loop_count: int

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, timeout=120, num_ctx=4096)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

# ───────────────────────────────────────────────────────────────────
# DETERMINISTIC TOOLS (Graph Navigators)
# ───────────────────────────────────────────────────────────────────
def execute_safe_cypher(query: str, params: dict, state: GraphState) -> str:
    """Executes cypher natively, extracts UI records, returns text summary for LLM."""
    summary = ""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            result = session.run(query, **params)
            
            records = []
            for record in result:
                # Add to UI results
                processed = {}
                for key, value in record.items():
                    if hasattr(value, "labels"): # Node
                        processed[key] = {"id": value.get("id"), "labels": list(value.labels), "properties": dict(value)}
                    elif hasattr(value, "type"): # Rel
                        processed[key] = {"id": f"{value.start_node.get('id')}-{value.end_node.get('id')}", "type": value.type, "properties": dict(value)}
                    else:
                        processed[key] = value
                records.append(processed)
                if "query_results" not in state:
                    state["query_results"] = []
                state["query_results"].append(processed)
            
            # Format text for LLM (just IDs and minor details to save token context)
            if not records:
                summary = "No results found."
            else:
                summary = f"Found {len(records)} matching nodes. " + ", ".join([str(r.get('o', {}).get('id') or r.get('p', {}).get('properties', {}).get('id') or r.get('c', {}).get('id')) for r in records[:5]])
        driver.close()
    except Exception as e:
        summary = f"Error: {str(e)}"
    return summary

def tool_search_customer(args_str: str, state: GraphState) -> str:
    kw = re.sub(r'[^\w\s]', '', args_str).strip()
    q = "CALL db.index.fulltext.queryNodes('customer_fts', $fts) YIELD node as c RETURN c LIMIT 3"
    return execute_safe_cypher(q, {"fts": f"*{kw}*"}, state)

def tool_search_product(args_str: str, state: GraphState) -> str:
    fts_query = " ".join([f"{k}~" for k in re.sub(r'[^\w\s]', '', args_str).split() if len(k) > 3])
    q = "CALL db.index.fulltext.queryNodes('product_fts', $fts) YIELD node as p RETURN p LIMIT 3"
    return execute_safe_cypher(q, {"fts": fts_query}, state)

def tool_get_orders_for_customer(args_str: str, state: GraphState) -> str:
    cid = args_str.strip()
    q = "MATCH (c:Customer {id: $id})-[r:PLACED]->(o:SalesOrder) RETURN c, r, o LIMIT 10"
    return execute_safe_cypher(q, {"id": cid}, state)

def tool_get_order_details(args_str: str, state: GraphState) -> str:
    oid = args_str.strip()
    q = "MATCH (o:SalesOrder {id: $id})-[r:HAS_ITEM]->(i:SalesOrderItem)-[r2:IS_PRODUCT]->(p:Product) RETURN o, r, i, r2, p"
    return execute_safe_cypher(q, {"id": oid}, state)

TOOLS = {
    "search_customer": tool_search_customer,
    "search_product": tool_search_product,
    "get_orders_for_customer": tool_get_orders_for_customer,
    "get_order_details": tool_get_order_details
}
# ───────────────────────────────────────────────────────────────────

def init_agent(state: GraphState) -> GraphState:
    if "history" not in state:
        state["history"] = []
    if "loop_count" not in state:
        state["loop_count"] = 0
    if "query_results" not in state:
        state["query_results"] = []
    return state

def reason_next_step(state: GraphState) -> GraphState:
    question = state["question"]
    history = "\n".join(state["history"]) if state["history"] else "None"
    
    if state["loop_count"] >= 4:
         return {"intent": "terminate"}
         
    prompt = PromptTemplate.from_template(
        "You are an O2C Search Agent exploring a graph database.\n"
        "Question: {question}\n\n"
        "TOOLS:\n"
        "- search_customer: <name>\n"
        "- search_product: <name>\n"
        "- get_orders_for_customer: <customer_id>\n"
        "- get_order_details: <order_id>\n"
        "- END: <answer text>\n\n"
        "History of your actions:\n{history}\n\n"
        "What is the exactly next single action? Format: CALL tool_name: argument\n"
        "Action:"
    )
    
    chain = prompt | llm
    try:
        res = chain.invoke({"question": question, "history": history})
        action_text = res.content.strip()
        state["history"].append(f"AI: {action_text}")
    except Exception as e:
        state["history"].append(f"AI ERROR: {str(e)}")
        return {"intent": "error", "error": str(e)}
        
    state["loop_count"] += 1
    return state

def execute_tool(state: GraphState) -> GraphState:
    last_action = state["history"][-1]
    
    if "CALL " in last_action:
        try:
            cmd = last_action.split("CALL ")[1]
            if ":" in cmd:
                tool_name, arg = cmd.split(":", 1)
                tool_name = tool_name.strip()
                arg = arg.strip()
                
                if tool_name in TOOLS:
                    res = TOOLS[tool_name](arg, state)
                    state["history"].append(f"OBSERVATION: {res}")
                else:
                    state["history"].append(f"OBSERVATION: Tool {tool_name} not found.")
            else:
                state["history"].append("OBSERVATION: Invalid CALL format. Use CALL tool_name: arg")
        except Exception:
            state["history"].append("OBSERVATION: Error parsing tool call.")
            
    return state

def should_continue(state: GraphState):
    if state.get("intent") == "error":
        return "summarize"
    last = state["history"][-1] if state.get("history") else ""
    if "END:" in last or state["loop_count"] >= 4:
        return "summarize"
    return "execute_tool"

def summarize(state: GraphState) -> GraphState:
    last = state["history"][-1] if state.get("history") else ""
    ans = last.split("END:", 1)[1].strip() if "END:" in last else "Could not reach an answer in time."
    state["final_response"] = ans
    return state

def build_agent():
    workflow = StateGraph(GraphState)
    workflow.add_node("init_agent", init_agent)
    workflow.add_node("reason_next_step", reason_next_step)
    workflow.add_node("execute_tool", execute_tool)
    workflow.add_node("summarize", summarize)
    
    workflow.set_entry_point("init_agent")
    workflow.add_edge("init_agent", "reason_next_step")
    workflow.add_conditional_edges("reason_next_step", should_continue, {
        "execute_tool": "execute_tool",
        "summarize": "summarize"
    })
    workflow.add_edge("execute_tool", "reason_next_step")
    workflow.add_edge("summarize", END)
    return workflow.compile()

agent = build_agent()

if __name__ == "__main__":
    initial_state = {"question": "Find orders for Bradley-Kelley"}
    final_state = agent.invoke(initial_state)
    print("\n--- FINAL HISTORY ---")
    for h in final_state.get("history", []):
         print(h)
    print("\nFINAL RESPONSE:", final_state.get("final_response"))
    print("RECORDS COLLECTED:", len(final_state.get("query_results", [])))
