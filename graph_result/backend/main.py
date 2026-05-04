from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from routers import graph, chat


app = FastAPI(title="Order-to-Cash Graph API", version="1.0.0")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.router, prefix="/api/graph", tags=["Graph exploration"])
app.include_router(chat.router, prefix="/api/chat", tags=["LangGraph Chat"])

@app.get("/")
def root():
    return {"message": "Welcome to the Order-to-Cash Graph API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
