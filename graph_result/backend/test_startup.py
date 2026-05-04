import sys
print("1. Starting...")
try:
    print("2. Importing FastAPI")
    from fastapi import FastAPI
    print("3. Importing CORSMiddleware")
    from fastapi.middleware.cors import CORSMiddleware
    print("4. Importing os")
    import os
    print("5. Importing load_dotenv")
    from dotenv import load_dotenv
    print("6. Calling load_dotenv()")
    load_dotenv()
    print("7. Importing routers.graph")
    from routers import graph
    print("8. Importing routers.chat")
    from routers import chat
    print("9. Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"FAILED: {e}")
