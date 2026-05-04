from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

llm = ChatOllama(model="deepseek-r1:1.5b", temperature=0, timeout=60, num_ctx=4096)

prompt = PromptTemplate.from_template(
    "TASK: Extract core product keywords or business names from the question. \n"
    "Normalize text and fix any spelling mistakes. Ignore filler words (the, and, for, etc.). \n"
    "Return ONLY the fixed keywords separated by spaces. Nothing else.\n\n"
    "Example Query: 'Which costomers orderd the almand and then brd oilll?'\n"
    "Output: almond thyme beard oil\n\n"
    "Query: '{question}'\nOutput:"
)

chain = prompt | llm
res = chain.invoke({"question": "Whic costumer orded the facewishh vit c?"})
print("Fixed Keywords:", res.content)
