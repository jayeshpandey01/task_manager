import sys
print("A. Starting")
try:
    print("B. Importing StateGraph")
    from langgraph.graph import StateGraph, END
    print("C. Importing PromptTemplate")
    from langchain_core.prompts import PromptTemplate
    print("D. Importing ChatOllama")
    from langchain_ollama import ChatOllama
    print("E. Importing Neo4j")
    from neo4j import GraphDatabase
    print("F. Instantiating ChatOllama")
    llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, timeout=60, num_ctx=4096)
    print("G. Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
