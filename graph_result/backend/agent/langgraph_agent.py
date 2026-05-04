from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from neo4j import GraphDatabase
import os
import requests

from dotenv import load_dotenv
load_dotenv()

# State Definition
class GraphState(TypedDict, total=False):
    question: str
    intent: Optional[str]        # 'domain_query', 'unsafe', 'general', 'error'
    cypher_query: Optional[str]
    query_results: Optional[List[dict]]
    table_data: Optional[List[dict]]  # Flattened table rows for UI and LLM grounding
    table_columns: Optional[List[str]]
    final_response: Optional[str]
    error: Optional[str]
    retry_count: Optional[int]
    discovered_entities: Optional[List[dict]] # List of {id, label} pairs
    history: Optional[List[dict]] # For multi-turn chat support
    reasoning_trace: Optional[str] # Chain of thought context

# Initialize Local Ollama model with retries
llm = ChatOllama(
    model="deepseek-r1:1.5b",
    temperature=0,
    timeout=60, # Increase timeout for local Ollama
    num_ctx=4096
)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

SCHEMA_CONTEXT = """
Node Labels & Properties:
- Customer {id, name, category, creationDate, isBlocked}
- SalesOrder {id, creationDate, totalNetAmount, transactionCurrency, overallDeliveryStatus, salesOrderType}
- SalesOrderItem {id, salesOrder, itemNumber, material, requestedQuantity, netAmount, currency, plant, storageLocation}
- SalesOrderScheduleLine {id, salesOrder, salesOrderItem, scheduleLineNumber, confirmedDeliveryDate, confirmedQuantity, unit}
- OutboundDelivery {id, creationDate, overallGoodsMovementStatus, overallPickingStatus, shippingPoint, actualGoodsMovementDate}
- OutboundDeliveryItem {id, deliveryDocument, itemNumber, actualDeliveryQuantity, deliveryQuantityUnit, plant, storageLocation, referenceSdDocument, referenceSdDocumentItem}
- BillingDocument {id, billingDocumentDate, totalNetAmount, transactionCurrency, isCancelled, billingDocumentType}
- BillingDocumentItem {id, billingDocument, material, billingQuantity, netAmount, referenceSdDocument, referenceSdDocumentItem}
- Product {id, type, group, baseUnit, netWeight, creationDate, description}
- AccountingDocument {id, companyCode, fiscalYear, clearingDate, amountInTransactionCurrency, transactionCurrency, postingDate, documentDate}
- Plant {id, name, salesOrganization, profitCenter, mrpType}
- StorageLocation {id, code, plantId}
- Address {id, cityName, streetName, country, postalCode, houseNumber}

Relationships:
- (Customer)-[:PLACED]->(SalesOrder)
- (SalesOrder)-[:HAS_ITEM]->(SalesOrderItem)
- (SalesOrderItem)-[:IS_PRODUCT]->(Product)
- (SalesOrderItem)-[:HAS_SCHEDULE_LINE]->(SalesOrderScheduleLine)
- (SalesOrderItem)-[:SHIPPED_FROM]->(Plant)
- (SalesOrderItem)-[:STORED_IN]->(StorageLocation)
- (OutboundDelivery)-[:HAS_ITEM]->(OutboundDeliveryItem)
- (OutboundDeliveryItem)-[:FULFILLS]->(SalesOrderItem)
- (OutboundDeliveryItem)-[:SHIPPED_FROM]->(Plant)
- (OutboundDeliveryItem)-[:STORED_IN]->(StorageLocation)
- (BillingDocument)-[:BILLED_TO]->(Customer)
- (BillingDocument)-[:HAS_ACCOUNTING_DOC]->(AccountingDocument)
- (BillingDocument)-[:HAS_ITEM]->(BillingDocumentItem)
- (BillingDocumentItem)-[:BILLS_FOR]->(OutboundDeliveryItem)
- (Customer)-[:PAID]->(AccountingDocument)
- (Plant)-[:HAS_ADDRESS]->(Address)
- (Customer)-[:HAS_ADDRESS]->(Address)
- (Plant)-[:HAS_STORAGE_LOCATION]->(StorageLocation)
- (Product)-[:PRODUCED_AT]->(Plant)
- (Product)-[:STORED_IN]->(StorageLocation)

Important Rules:
1. IDs are strings (e.g. '740506').
2. SalesOrder does NOT have a 'status' property. Use 'overallDeliveryStatus' instead ('A' means Open/Not Processed, 'C' means Completed/Closed).
3. If a user asks for 'orders for customer X', search (Customer {id: 'X'})-[:PLACED]->(o:SalesOrder).
4. Address properties (streetName, cityName, country) are ONLY on the Address node. To find a Plant's address, you MUST join: (p:Plant)-[:HAS_ADDRESS]->(a:Address).
5. Relationships are typed. Use upper case (e.g., :PLACED, :HAS_ITEM).
6. Plants and Customers can have Addresses via :HAS_ADDRESS.
"""

def detect_intent(state: GraphState) -> GraphState:
    question = state["question"].lower()
    
    unsafe_keywords = ["delete", "remove", "drop", "truncate", "alter", "set ", "merge ", "insert "]
    for kw in unsafe_keywords:
        if kw in question:
            return {"intent": "unsafe"}
            
    general_keywords = ["joke", "weather", "hello", "hi", "how are you", "write code", "python", "javascript"]
    if any(question.startswith(kw) for kw in general_keywords):
        return {"intent": "general"}
        
    return {"intent": "domain_query"}


def discover_entities(state: GraphState) -> GraphState:
    import re
    question = state["question"]
    # Simple regex to find potential IDs (numeric or alphanumeric)
    # Looking for chunks that look like IDs (e.g., 740506, 310000108, 5000000021)
    potential_ids = re.findall(r'\b\d{5,12}\b', question)
    
    if not potential_ids:
        return {"discovered_entities": []}
    
    discovered = []
    
    # Use the configured embedding model from env
    def get_embedding(text, model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")):
        try:
            url = f"{os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')}/api/embeddings"
            # Nomic models prefer prefixes
            prefix = "search_query: " if "nomic" in model.lower() else ""
            response = requests.post(url, json={"model": model, "prompt": prefix + text}, timeout=15)
            response.raise_for_status()
            return response.json().get("embedding")
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            # 1. Exact ID Search (Highest Priority)
            for pid in potential_ids:
                result = session.run(
                    "MATCH (n) WHERE n.id = $id RETURN labels(n) as labels, n.id as id LIMIT 1",
                    id=pid
                )
                record = result.single()
                if record:
                    discovered.append({"id": record["id"], "labels": record["labels"]})
            
            # 2. Vector-Less Fuzzy Match (Neo4j Full-Text Search fallback)
            # This implements "fuzzy" matching for descriptions and categories WITHOUT vectors.
            if not discovered or len(discovered) == 0:
                print(f"No exact IDs found. Performing Vector-less Fuzzy Search for: '{question}'")
                import re
                clean_q = re.sub(r'[^\w\s]', '', question)
                # Filter out stop words and keep keywords for fuzzy search
                stopwords = {'what', 'is', 'the', 'status', 'of', 'show', 'me', 'which', 'who', 'ordered', 'for', 'are', 'did', 'having', 'with'}
                keywords = [k for k in clean_q.split() if k.lower() not in stopwords and len(k) >= 3]
                
                if keywords:
                    # attach Lucene ~ fuzzy operator (e.g. "almond~") to each keyword
                    fuzzy_query = " ".join([f"{k}~" for k in keywords])
                    
                    try:
                        # Search Product Descriptions Fuzzy
                        product_results = session.run("""
                            CALL db.index.fulltext.queryNodes('product_fts', $fuzzy_query) 
                            YIELD node, score 
                            WHERE score > 0.1 
                            RETURN node.id as id, labels(node) as labels, node.description as desc LIMIT 3
                        """, fuzzy_query=fuzzy_query)
                        for r in product_results:
                            discovered.append({"id": r["id"], "labels": r["labels"], "semantic": f"FTS Fuzz Product: {r['desc']}"})
                            
                        # Search Customer Categories Fuzzy
                        customer_results = session.run("""
                            CALL db.index.fulltext.queryNodes('customer_fts', $fuzzy_query) 
                            YIELD node, score 
                            WHERE score > 0.1 
                            RETURN node.id as id, labels(node) as labels, node.category as cat LIMIT 3
                        """, fuzzy_query=fuzzy_query)
                        for r in customer_results:
                            discovered.append({"id": r["id"], "labels": r["labels"], "semantic": f"FTS Fuzz Category: {r['cat']}"})
                    except Exception as e:
                        print(f"FTS Fuzzy search failed: {e}")

        driver.close()
    except Exception as e:
        print(f"Error in entity discovery: {e}")
        
    return {"discovered_entities": discovered}


# ── Deterministic query templates for common patterns ────────────────────
# Avoids LLM entirely for well-known query shapes, preventing hallucination.
QUERY_TEMPLATES = [
    # Summary of an order (Flexible regex for typos)
    (r"sum.*?\s+.*?or.*?\s+(\d+)|or.*?\s+(\d+).*sum.*?",
     lambda m: f"MATCH (o:SalesOrder {{id: '{m.group(1) or m.group(2)}'}}) "
               f"OPTIONAL MATCH (o)-[r1:HAS_ITEM]->(i:SalesOrderItem) "
               f"OPTIONAL MATCH (i)-[r2:IS_PRODUCT]->(p:Product) "
               f"RETURN o, r1, i, r2, p"),
    # Items in order
    (r"it.*?\s+in\s+.*?or.*?\s+(\d+)|or.*?\s+(\d+).*it.*?",
     lambda m: f"MATCH (o:SalesOrder {{id: '{m.group(1) or m.group(2)}'}}) "
               f"-[r:HAS_ITEM]->(i:SalesOrderItem) RETURN o, r, i"),
    # Orders for customer
    (r"ord.*?\s+(?:for|of|by)\s+(?:cust.*?\s+)?(\d+)",
     lambda m: f"MATCH (c:Customer {{id: '{m.group(1)}'}}) "
               f"-[r:PLACED]->(o:SalesOrder) RETURN c, r, o"),
    # Delivery status of order
    (r"(?:del.*?\s+stat.*?|stat.*?)\s+.*?or.*?\s+(\d+)|or.*?\s+(\d+).*?(?:del.*?\s+stat.*?|stat.*?)",
     lambda m: f"MATCH (o:SalesOrder {{id: '{m.group(1) or m.group(2)}'}}) "
               f"RETURN o, o.overallDeliveryStatus"),
    # Plant address
    (r"addr.*?\s+.*?plant.*?\s+(\d+)|plant.*?\s+(\d+).*?addr.*?",
     lambda m: f"MATCH (p:Plant {{id: '{m.group(1) or m.group(2)}'}}) "
               f"-[r:HAS_ADDRESS]->(a:Address) RETURN p, r, a"),
    # Customer address
    (r"addr.*?\s+.*?cust.*?\s+(\d+)|cust.*?\s+(\d+).*?addr.*?",
     lambda m: f"MATCH (c:Customer {{id: '{m.group(1) or m.group(2)}'}}) "
               f"-[r:HAS_ADDRESS]->(a:Address) RETURN c, r, a"),
    # Billing / invoice for order
    (r"(?:bill.*?|inv.*?)\s+.*?or.*?\s+(\d+)|or.*?\s+(\d+).*?(?:bill.*?|inv.*?)",
     lambda m: f"MATCH (o:SalesOrder {{id: '{m.group(1) or m.group(2)}'}}) "
               f"-[r1:HAS_ITEM]->(i:SalesOrderItem)<-[r2:FULFILLS]-(di:OutboundDeliveryItem) "
               f"<-[r3:BILLS_FOR]-(bi:BillingDocumentItem)<-[r4:HAS_ITEM]-(b:BillingDocument) "
               f"RETURN o, r1, i, r2, di, r3, bi, r4, b"),
    # Orders shipped from plant in delivery status
    (r"ord.*?\s+.*?shipped.*?\s+.*?plant.*?\s+(\d+).*?in\s+'?([a-zA-Z]+)'?\s+deliv.*?\s+stat.*?",
     lambda m: f"MATCH (o:SalesOrder {{overallDeliveryStatus: '{'A' if m.group(2).lower() == 'open' else 'C' if m.group(2).lower() in ['closed', 'completed', 'c'] else m.group(2).title()}'}})-[r1:HAS_ITEM]->(i:SalesOrderItem)-[r2:SHIPPED_FROM]->(p:Plant {{id: '{m.group(1)}'}}) RETURN o, r1, i, r2, p LIMIT 50"),
    # Items in delivery
    (r"(?:it.*?\s+.*?del.*?\s+(\d+))|(?:del.*?\s+(\d+).*?it.*?)",
     lambda m: f"MATCH (d:OutboundDelivery {{id: '{m.group(1) or m.group(2)}'}}) "
               f"-[r1:HAS_ITEM]->(di:OutboundDeliveryItem) "
               f"-[r2:FULFILLS]->(si:SalesOrderItem) "
               f"RETURN d, r1, di, r2, si"),
    # Customers ordered specific product (Advanced FTS search)
    (r"(?:who|which|what|show|list)?\s*(?:cust.*?|user.*?)\s+(?:who\s+|that\s+)?order.*?\s+(?:the\s+)?(.*)$",
     lambda m: "CALL db.index.fulltext.queryNodes('product_fts', '" + " ".join([f"{k}~" for k in __import__('re').sub(r'[^\w\s]', '', m.group(1)).split() if len(k) > 3]) + "') YIELD node AS p WITH p MATCH (c:Customer)-[r1:PLACED]->(o:SalesOrder)-[r2:HAS_ITEM]->(i:SalesOrderItem)-[r3:IS_PRODUCT]->(p) RETURN c, r1, o, r2, i, r3, p LIMIT 50"),
]

def try_template_match(question: str):
    """Return a ready-made Cypher query if question matches a template, else None."""
    import re
    q = question.lower()
    for pattern, builder in QUERY_TEMPLATES:
        m = re.search(pattern, q)
        if m:
            try:
                return builder(m)
            except Exception:
                continue
    return None


def generate_cypher(state: GraphState) -> GraphState:
    question = state["question"]
    error = state.get("error") # Check if we are in a retry/repair loop
    current_retries = state.get("retry_count", 0)
    
    if current_retries >= 3:
        return {"error": f"Failed to generate valid Cypher after 3 attempts. Last error: {error}"}
    
    repair_context = ""
    if error and state.get("cypher_query"):
        repair_context = f"\n\nPREVIOUS FAILED QUERY: {state['cypher_query']}\nERROR: {error}\nFIX THE QUERY ABOVE. Do NOT use the variable `p` for two different things."

    # ── Fast path: try deterministic template before calling LLM ──────────
    if not repair_context:  # Only skip LLM on first attempt (not during repair)
        template_cypher = try_template_match(question)
        if template_cypher:
            print(f"[Template Match] Using pre-built query: {template_cypher}")
            return {"cypher_query": template_cypher, "error": None, "retry_count": current_retries + 1}

    prompt = PromptTemplate(
        input_variables=["schema", "entities", "question", "repair_context"],
        template=(
            "You are a strict Cypher query generator for a Neo4j database.\n"
            "SCHEMA CONTEXT:\n{schema}\n\n"
            "DISCOVERED ENTITIES:\n{entities}\n\n"
            "RULES:\n"
            "1. Output ONLY 'Reasoning: <text>' and 'Cypher: <query>'.\n"
            "2. DO NOT explain the query outside the Reasoning block.\n"
            "3. Use toLower() for contains searches: WHERE toLower(p.description) CONTAINS toLower('term')\n"
            "4. NEVER output markdown symbols (```).\n"
            "5. NO hallucinated Cypher syntax (no regex patterns or CALL? blocks).\n\n"
            "LAWS OF NAVIGATION:\n"
            "- To find why an order isn't delivered: MATCH (o:SalesOrder)-[:HAS_ITEM]->(i:SalesOrderItem)<-[:FULFILLS]-(di:OutboundDeliveryItem)\n"
            "- To find what a customer bought: MATCH (c:Customer)-[:PLACED]->(o:SalesOrder)-[:HAS_ITEM]->(i:SalesOrderItem)-[:IS_PRODUCT]->(p:Product)\n"
            "- To find where a product is stored: MATCH (p:Product)-[:STORED_AT]->(s:StorageLocation)-[:BELONGS_TO]->(pl:Plant)\n\n"
            "Question: {question}{repair_context}\n"
            "Response:\n"
            "Reasoning: <step-by-step navigation>\n"
            "Cypher: MATCH ... RETURN ..."
        )
    )
    chain = prompt | llm
    
    entities_str = "None"
    if state.get("discovered_entities"):
        entities_str = ", ".join([f"{e['id']} (Label: {e['labels'][0]})" for e in state["discovered_entities"]])

    res = chain.invoke({
        "schema": SCHEMA_CONTEXT, 
        "question": question, 
        "repair_context": repair_context,
        "entities": entities_str
    })
    
    # Clean up reasoning and cypher blocks
    raw_content = res.content.strip()
    reasoning_trace = ""
    cypher = ""
    
    if "Cypher:" in raw_content:
        # Split by the last occurrence of Cypher: to avoid matches in reasoning
        parts = raw_content.rsplit("Cypher:", 1)
        reasoning_trace = parts[0].replace("Reasoning:", "").strip()
        cypher = parts[1].strip()
    else:
        # Fallback if model missed the prefix
        cypher = raw_content

    # ── Advanced Sanitizer for 1.5B Hallucinations ──
    # 1. Strip common reasoning sentences if they leaked into the query
    cypher = cypher.split("Finally,")[0].split("This will help")[0].split("**")[0].strip()
    
    # 2. Fix common relationship hallucinations
    cypher = cypher.replace("IS.Product", "IS_PRODUCT")
    cypher = cypher.replace("IS.PRODUCT", "IS_PRODUCT")
    
    # 3. Extract only the valid Cypher block if it's surrounded by text
    import re
    match = re.search(r"(?is)(MATCH\b.*?\bRETURN\b.*?(?:(?=\n)|(?=\.)|$))", cypher)
    if match:
        cypher = match.group(1).strip()

    
    # 1B Model Protection: If cypher is still messy, try one last strict extraction
    if not cypher.upper().startswith("MATCH"):
        match_return = re.search(r"(?is)(MATCH\b.*?\bRETURN\b.*?(?:(?=\n)|(?=\.)|(?= is )|$))", raw_content)
        if match_return:
            cypher = match_return.group(1).strip()
    
    # Clean up any trailing semicolon
    if cypher.endswith(";"):
        cypher = cypher[:-1]
        
    return {"cypher_query": cypher, "error": None, "retry_count": current_retries + 1, "reasoning_trace": reasoning_trace}


def validate_cypher(state: GraphState) -> GraphState:
    query = state.get("cypher_query", "").upper()
    unsafe_keywords = ["DELETE", "DETACH", "REMOVE", "SET", "MERGE", "CREATE", "DROP"]
    
    for kw in unsafe_keywords:
        if f" {kw} " in f" {query} " or query.startswith(kw):
            return {"error": f"Unsafe query detected. Cannot execute operation containing {kw}."}
    
    return state


def execute_cypher(state: GraphState) -> GraphState:
    if state.get("error"):
        return state
        
    query = state["cypher_query"]
    print(f"Executing Cypher: {query}")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        records = []
        with driver.session() as session:
            result = session.run(query)
            for record in result:
                # Process each value in the record to handle Nodes/Relationships/Paths
                processed_record = {}
                for key, value in record.items():
                    if hasattr(value, "labels"): # It's a Node
                        processed_record[key] = {
                            "id": value.get("id"),
                            "labels": list(value.labels),
                            "properties": dict(value)
                        }
                    elif hasattr(value, "type"): # It's a Relationship
                        processed_record[key] = {
                            "id": f"{value.start_node.get('id')}-{value.end_node.get('id')}",
                            "type": value.type,
                            "source": value.start_node.get("id"),
                            "target": value.end_node.get("id"),
                            "properties": dict(value)
                        }
                    elif hasattr(value, "nodes") and hasattr(value, "relationships"): # It's a Path
                        path_data = {"nodes": [], "relationships": []}
                        for node in value.nodes:
                            path_data["nodes"].append({
                                "id": node.get("id"),
                                "labels": list(node.labels),
                                "properties": dict(node)
                            })
                        for rel in value.relationships:
                            path_data["relationships"].append({
                                "id": f"{rel.start_node.get('id')}-{rel.end_node.get('id')}",
                                "type": rel.type,
                                "source": rel.start_node.get("id"),
                                "target": rel.end_node.get("id"),
                                "properties": dict(rel)
                            })
                        processed_record[key] = path_data
                    else:
                        processed_record[key] = value
                records.append(processed_record)
        driver.close()
        return {"query_results": records}
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "final_response": "The AI is currently at its limit (Rate Limit). Please wait a few seconds and try again.",
                "intent": "error", # Set intent to error to bypass further processing
                "error": "Groq API Rate Limit Exceeded"
            }
        return {"error": error_msg}


def build_table_from_results(results: List[dict]):
    """Flatten Neo4j node/relationship results into clean table rows.
    Returns (rows: List[dict], columns: List[str])."""
    rows = []
    columns_set = []

    for record in results:
        row = {}
        for key, value in record.items():
            if value is None:
                continue
            if isinstance(value, dict):
                if "labels" in value and "properties" in value:
                    # It's a serialized Node
                    label = value["labels"][0] if value.get("labels") else key
                    props = value.get("properties", {})
                    for prop_k, prop_v in props.items():
                        col_name = f"{label}_{prop_k}" # Use underscore for clarity
                        row[col_name] = prop_v
                        if col_name not in columns_set:
                            columns_set.append(col_name)
                elif "nodes" in value and "relationships" in value:
                    # It's a Path — extract node properties from each node
                    for node in value.get("nodes", []):
                        label = node["labels"][0] if node.get("labels") else "Node"
                        for prop_k, prop_v in node.get("properties", {}).items():
                            col_name = f"{label}_{prop_k}"
                            row[col_name] = prop_v
                            if col_name not in columns_set:
                                columns_set.append(col_name)
                elif "type" in value and "source" in value and "target" in value:
                    # It's a Relationship — skip for table (shown in graph)
                    pass
                else:
                    # Generic dict
                    row[key] = str(value)
                    if key not in columns_set:
                        columns_set.append(key)
            else:
                # Primitive value
                row[key] = value
                if key not in columns_set:
                    columns_set.append(key)
        if row:
            rows.append(row)

    return rows, columns_set


def extract_table(state: GraphState) -> GraphState:
    """Explicit node for flattening results into a browser-ready table."""
    results = state.get("query_results")
    if not results:
        return {"table_data": [], "table_columns": []}
        
    table_rows, table_columns = build_table_from_results(results)
    return {"table_data": table_rows, "table_columns": table_columns}


def generate_response(state: GraphState) -> GraphState:
    import time
    time.sleep(0.5) 
    question = state.get("question", "")
    intent = state.get("intent")
    error = state.get("error")
    table_rows = state.get("table_data", [])
    table_columns = state.get("table_columns", [])

    if intent == 'unsafe':
        return {"final_response": "I'm sorry, I cannot perform unsafe data modifications or deletions."}
    if intent == 'general':
        return {"final_response": "I can only assist with queries related to the Order-to-Cash business graph domain."}

    if error and not table_rows:
        return {"final_response": f"I couldn't retrieve that data. Error: {error}"}

    if not table_rows:
        return {"final_response": "No matching records found."}

    # --- Step 2: Format table as text for the LLM prompt ---
    header = " | ".join(table_columns)
    separator = "-" * len(header)
    data_lines = []
    for row in table_rows[:5]:  # Cap to strictly avoid local Ollama 500 context crashes
        line = " | ".join(str(row.get(col, "")) for col in table_columns)
        data_lines.append(line)
    table_text = f"{header}\n{separator}\n" + "\n".join(data_lines)

    prompt = PromptTemplate(
        input_variables=["question", "table_text"],
        template=(
            "You are a helpful business assistant.\n"
            "Your task is to provide a single, simple paragraph answering the question based ONLY on the data below.\n"
            "If the table is empty, just say you couldn't find the data.\n\n"
            "DATA:\n{table_text}\n\n"
            "USER QUESTION: {question}\n\n"
            "INSTRUCTIONS:\n"
            "1. Write exactly ONE simple paragraph.\n"
            "2. DO NOT use bullet points, lists, or headers (no ### headers).\n"
            "3. Use plain English—keep it easy to read.\n"
            "4. Use **Bold** for any specific IDs or amounts.\n\n"
            "Response:"
        )
    )
    chain = prompt | llm
    try:
        res = chain.invoke({"question": question, "table_text": table_text})
        final_str = res.content.strip()
            
        reasoning = state.get("reasoning_trace")
        if reasoning:
            reasoning_block = f"🤖 **Agentic Root-to-Leaf Reasoning:**\n*{reasoning}*\n\n"
            final_str = reasoning_block + final_str
            
        return {"final_response": final_str}
    except Exception as e:
        import traceback
        err_msg = f"Error in LLM summary: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        return {"final_response": f"Found {len(table_rows)} records, but summary failed. Trace: {str(e)[:100]}..."}


def build_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("discover_entities", discover_entities)
    workflow.add_node("generate_cypher", generate_cypher)
    workflow.add_node("validate_cypher", validate_cypher)
    workflow.add_node("execute_cypher", execute_cypher)
    workflow.add_node("extract_table", extract_table)
    workflow.add_node("generate_response", generate_response)
    
    workflow.set_entry_point("detect_intent")
    
    def condition_on_intent(state: GraphState):
        intent = state.get("intent")
        if intent == "domain_query":
            return "discover_entities"
        return "generate_response"
        
    workflow.add_conditional_edges(
        "detect_intent",
        condition_on_intent,
        {
            "discover_entities": "discover_entities",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_edge("discover_entities", "generate_cypher")
    workflow.add_edge("generate_cypher", "validate_cypher")
    
    def condition_after_execution(state: GraphState):
        error = state.get("error")
        if error and isinstance(error, str) and "syntax" in error.lower():
            return "generate_cypher" 
        return "extract_table"

    def condition_on_validation(state: GraphState):
        if state.get("error"):
            return "generate_response"
        return "execute_cypher"
        
    workflow.add_conditional_edges(
        "validate_cypher",
        condition_on_validation,
        {
            "execute_cypher": "execute_cypher",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_cypher",
        condition_after_execution,
        {
            "generate_cypher": "generate_cypher",
            "extract_table": "extract_table"
        }
    )
    workflow.add_edge("extract_table", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()

graph_agent = build_graph()

def invoke_agent(question: str) -> dict:
    initial_state = {"question": question}
    try:
        final_state = graph_agent.invoke(initial_state)
        return {
            "intent": final_state.get("intent"),
            "cypher_query": final_state.get("cypher_query"),
            "results": final_state.get("query_results"),
            "table": final_state.get("table_data"),   # Validated flat table for UI
            "response": final_state.get("final_response"),
            "error": final_state.get("error")
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "rate_limit" in error_msg:
            return {
                "response": "The AI is currently at its limit (Rate Limit). Please wait a minute and try again.",
                "intent": "error",
                "error": "Groq API Rate Limit Exceeded"
            }
        return {"error": error_msg, "response": f"An error occurred: {error_msg}"}
