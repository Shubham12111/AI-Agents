from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.get("/health")
def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=200)