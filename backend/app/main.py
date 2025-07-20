from fastapi import FastAPI, UploadFile, File, Response
from sqlalchemy import text
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.agent import run_agent
from app.preprocessing import preprocess_text
from app.routers.routes import router
from app.routers import intent, chat, rag_chat, websocket
from app.database import engine
from app.services.OpenAIClient import OpenAIClient
from app.services.Serper import SerperClient
from app.models.intent import Intent

import os
load_dotenv()

app = FastAPI()

# Routers
app.include_router(intent.router)
app.include_router(chat.router, prefix="/api")
app.include_router(rag_chat.router, prefix="/api")
app.include_router(router)
app.include_router(websocket.router)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3029"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Sec-WebSocket-Accept"]
)

# Clients
serper_client = SerperClient()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("❌ OPENAI_API_KEY is not set.")
openai_client = OpenAIClient(openai_api_key)

@app.on_event("startup")
async def startup():
    print("Connecting to database and creating tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Intent.metadata.create_all)
        print("✅ DB connection and table creation successful.")
    except Exception as e:
        print("❌ DB connection failed:", str(e))

@app.get("/")
async def health_check():
    print("Health check passed!")
    return Response(status_code=200)

@app.get("/openai")
def openai_api_call(model: str = "gpt-4", question: str = "What is the capital of France?"):
    openai_client.set_model(model)
    answer = openai_client.generate_response(question)
    return {"answer": answer}

@app.post("/run-agent")
async def run_agent_route(prompt: str):
    response = run_agent(prompt)
    return {"response": response}

@app.post("/preprocess")
async def preprocess_route(text: str):
    cleaned = preprocess_text(text)
    return {"cleaned_text": cleaned}

@app.post("/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    return {"status": "Knowledge ingested", "lines": len(text.splitlines())}
