# Not Used
from fastapi import APIRouter, UploadFile, File
from app.agent import run_agent
from app.preprocessing import preprocess_text

router = APIRouter()

@router.post("/run-agent/")
async def run_agent_route(prompt: str):
    response = run_agent(prompt)
    return {"response": response}

@router.post("/preprocess/")
async def preprocess_route(text: str):
    cleaned = preprocess_text(text)
    return {"cleaned_text": cleaned}

@router.post("/upload-knowledge/")
async def upload_knowledge(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    # (Optional) Preprocess or store
    return {"status": "Knowledge ingested", "lines": len(text.splitlines())}
