from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from datetime import datetime

from services.routes_service import (
    health_service,
    keyword_service,
    generation_service,
    pdf_service,
)
from services.logger_service import LoggerUtils, LogLevel
from services.orchestration.tools.mongo import (
    save_search_topic_to_mongodb,
    get_pending_search_topics,
    update_search_topic_status,
    search_topics_collection,
)
from services.agent_service.run_analysis import run_analysis_workflow

from factory import MONGO_SERVICE, NOTION_SERVICE

# Initialize the logger
logger = LoggerUtils("main_file", LogLevel.DEBUG)

# Initialize the FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_service.router)
app.include_router(keyword_service.router)
app.include_router(generation_service.router)
app.include_router(pdf_service.router)


# Define request models
class TopicRequest(BaseModel):
    topic: str


@app.post("/topics/search")
async def create_search_topic(request: TopicRequest):
    """
    Endpoint to save a new search topic and trigger the analysis workflow.
    """
    try:
        # Save the topic to MongoDB
        topic_id = save_search_topic_to_mongodb(request.topic)

        # Trigger the analysis workflow asynchronously
        asyncio.create_task(process_topic(topic_id, request.topic))

        return {
            "status": "success",
            "message": "Topic saved and analysis started",
            "topic_id": topic_id,
        }
    except Exception as e:
        logger.error(f"Error creating search topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topics/pending")
async def get_pending_topics():
    """
    Endpoint to get all pending search topics.
    """
    try:
        pending_topics = get_pending_search_topics()
        return {"status": "success", "topics": pending_topics}
    except Exception as e:
        logger.error(f"Error getting pending topics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_topic(topic_id: str, topic: str):
    """
    Process a search topic asynchronously.
    """
    try:
        logger.info(f"Starting analysis workflow for topic: {topic}")
        # Run the analysis workflow with the topic
        collection_id = run_analysis_workflow(topic)

        if not collection_id:
            raise Exception("Analysis workflow did not return a collection ID")

        # Update the topic status to completed with results
        search_topics_collection.update_one(
            {"id": topic_id},
            {
                "$set": {
                    "status": "completed",
                    "collection_id": collection_id,
                    "completed_at": datetime.now(),
                    "result": "Analysis completed successfully",
                }
            },
        )
        logger.info(f"Topic analysis completed. Collection ID: {collection_id}")

        # Verify the update was successful
        updated_topic = search_topics_collection.find_one({"id": topic_id})
        if updated_topic and updated_topic.get("status") != "completed":
            logger.error(
                f"Failed to update topic status to completed. Current status: {updated_topic.get('status')}"
            )
            raise Exception("Failed to update topic status")

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing topic: {error_message}")
        # Update the topic status to failed with error message
        search_topics_collection.update_one(
            {"id": topic_id},
            {
                "$set": {
                    "status": "failed",
                    "error": error_message,
                    "completed_at": datetime.now(),
                }
            },
        )
        raise  # Re-raise the exception to ensure it's properly handled


@app.get("/topics/{topic_id}/status")
async def get_topic_status(topic_id: str):
    """
    Endpoint to get the status of a specific topic analysis.
    """
    try:
        topic = search_topics_collection.find_one({"id": topic_id})
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        status_response = {
            "status": topic.get("status"),
            "topic": topic.get("topic"),
            "created_at": topic.get("created_at"),
            "completed_at": topic.get("completed_at"),
        }

        # Add additional fields based on status
        if topic.get("status") == "completed":
            status_response.update(
                {
                    "collection_id": topic.get("collection_id"),
                    "result": topic.get("result"),
                }
            )
        elif topic.get("status") == "failed":
            status_response["error"] = topic.get("error")

        return {"status": "success", "data": status_response}
    except Exception as e:
        logger.error(f"Error getting topic status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Initialize MongoDB and Notion services before running the app
def init_services():
    logger.info("Initializing services")
    app.state.mongo_service = MONGO_SERVICE
    app.state.notion_service = NOTION_SERVICE


# Run the app programmatically
if __name__ == "__main__":

    # logger.debug("Application started")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

    # logger.info("Application finished")
