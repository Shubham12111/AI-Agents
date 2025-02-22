from fastapi import FastAPI
import asyncio
from typing import Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from fastapi import FastAPI, File, UploadFile
from PyPDF2 import PdfReader
import io

router = APIRouter()

@router.post("/pdfreader")
async def extract_text(file: UploadFile = File(...)):
    # Read the uploaded file
    contents = await file.read()
    
    # Extract text from PDF
    text = ""
    pdf_reader = PdfReader(io.BytesIO(contents))
    for page in pdf_reader.pages:
        text += page.extract_text() or ""  # Handle pages with no text



