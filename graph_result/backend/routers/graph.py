from fastapi import APIRouter, HTTPException
from neo4j import GraphDatabase
import os

router = APIRouter()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

def get_driver():
    return GraphDatabase.driver(URI, auth=AUTH)

@router.get("/metadata")
def get_graph_metadata():
    query = """
    CALL db.labels() YIELD label 
    RETURN collect(label) AS labels
    """
    try:
        with get_driver() as driver:
            with driver.session() as session:
                result = session.run(query)
                labels = result.single()["labels"]
        return {"labels": labels}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neighbors/{node_id}")
def get_node_neighbors(node_id: str):
    # This fetches 1-hop neighbors for visualization
    query = """
    MATCH (n {id: $node_id})-[r]-(m)
    RETURN n, r, m
    """
    try:
        nodes = {}
        edges = []
        with get_driver() as driver:
            with driver.session() as session:
                result = session.run(query, node_id=node_id)
                for record in result:
                    n = record["n"]
                    m = record["m"]
                    r = record["r"]
                    
                    if n["id"] not in nodes:
                        nodes[n["id"]] = {"id": n["id"], "labels": list(n.labels), "properties": dict(n)}
                    if m["id"] not in nodes:
                        nodes[m["id"]] = {"id": m["id"], "labels": list(m.labels), "properties": dict(m)}
                        
                    edges.append({
                        "source": n["id"],
                        "target": m["id"],
                        "type": r.type
                    })
        return {"nodes": list(nodes.values()), "edges": edges}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
def get_graph_overview():
    # Fetch a meaningful graph showing an end-to-end O2C process flow
    query = """
    MATCH (c:Customer)-[r1:PLACED]->(o:SalesOrder)-[r2:HAS_ITEM]->(oi:SalesOrderItem)
    WITH c, r1, o, r2, oi LIMIT 3
    OPTIONAL MATCH (oi)<-[r3:FULFILLS]-(di:OutboundDeliveryItem)<-[r4:HAS_ITEM]-(d:OutboundDelivery)
    OPTIONAL MATCH (oi)-[r5:IS_PRODUCT]->(p:Product)
    OPTIONAL MATCH (di)<-[r6:BILLS_FOR]-(bi:BillingDocumentItem)<-[r7:HAS_ITEM]-(b:BillingDocument)
    OPTIONAL MATCH (b)-[r8:HAS_ACCOUNTING_DOC]->(a:AccountingDocument)
    RETURN c, r1, o, r2, oi, r3, di, r4, d, r5, p, r6, bi, r7, b, r8, a
    """
    try:
        nodes = {}
        edges = []
        with get_driver() as driver:
            with driver.session() as session:
                result = session.run(query)
                for record in result:
                    # Parse all nodes and relationships returned dynamically
                    for key in record.keys():
                        val = record[key]
                        if not val:
                            continue
                        if hasattr(val, "labels"):  # Node
                            if val["id"] not in nodes:
                                nodes[val["id"]] = {"id": val["id"], "labels": list(val.labels), "properties": dict(val)}
                        elif hasattr(val, "type"):  # Relationship
                            edge_id = f"{val.start_node['id']}-{val.end_node['id']}-{val.type}"
                            edges.append({
                                "source": val.start_node["id"],
                                "target": val.end_node["id"],
                                "type": val.type,
                                "id": edge_id
                            })
        # Remove duplicate edges
        unique_edges = {e['id']: e for e in edges}.values()
        return {"nodes": list(nodes.values()), "edges": list(unique_edges)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
def search_nodes(q: str):
    # Fuzzy search by ID or name
    # Search for matching nodes AND their neighbors for context
    query = """
    MATCH (n)
    WHERE n.id CONTAINS $q OR (n.name IS NOT NULL AND n.name CONTAINS $q)
    WITH n LIMIT 5
    OPTIONAL MATCH (n)-[r]-(m)
    RETURN n, r, m
    """
    try:
        nodes = {}
        edges = []
        with get_driver() as driver:
            with driver.session() as session:
                result = session.run(query, q=q)
                for record in result:
                    n = record["n"]
                    m = record["m"]
                    r = record["r"]
                    
                    if n and n["id"] not in nodes:
                        nodes[n["id"]] = {"id": n["id"], "labels": list(n.labels), "properties": dict(n)}
                    if m and m["id"] not in nodes:
                        nodes[m["id"]] = {"id": m["id"], "labels": list(m.labels), "properties": dict(m)}
                    if r:
                        edges.append({"source": n["id"], "target": m["id"], "type": r.type})
                        
        return {"nodes": list(nodes.values()), "edges": edges}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
