from fastapi import FastAPI
import asyncio
from typing import Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.agent_service.run_analysis import run_analysis_workflow

router = APIRouter()

async def run_analysis_task():
    """Runs `run_analysis_workflow()` in a separate thread to avoid blocking FastAPI."""
    try:
        loop = asyncio.get_running_loop()
        collection_id = await loop.run_in_executor(None, run_analysis_workflow)  # Run in a worker thread
        print(f"\nAll results have been saved to MongoDB with collection ID: {collection_id}")
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")

@router.post("/generation")
async def start_analysis():
    """Trigger analysis in the background without blocking other routes."""
    try:
        # Run the analysis task in the background
        asyncio.create_task(run_analysis_task())
        return JSONResponse(content={"message": "Analysis task started in the background."}, status_code=202)
    except Exception as e:
        return JSONResponse(content={"error": f"Error during analysis: {str(e)}"}, status_code=500)


# @router.get("/generation")
# async def start_analysis():
#     try:
#         collection_id = run_analysis_workflow()
#         print(
#             f"\nAll results have been saved to MongoDB with collection ID: {collection_id}"
#         )
#     except Exception as e:
#         print(f"\nError during analysis: {str(e)}")
