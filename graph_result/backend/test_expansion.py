from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, timeout=60, num_ctx=4096)

prompt = PromptTemplate.from_template(
    "You are a search query enhancement tool.\n"
    "TASK:\n"
    "1. Fix any spelling errors in the user's text.\n"
    "2. Expand the query with 2-3 related synonyms (e.g., 'facewash' -> 'face wash cleanser skincare').\n"
    "3. Return ONLY the enhanced space-separated keyword string.\n\n"
    "Input Query: 'Whic costumers ordrd the facewishh vit c'\n"
    "Enhanced Query:"
)

chain = prompt | llm
res = chain.invoke({})
print("Expansion Result:", res.content)
