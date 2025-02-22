from pymongo import MongoClient
from services.logger_service import LoggerUtils, LogLevel

logger = LoggerUtils("MongoDBInit", LogLevel.DEBUG)


def init_mongodb():
    """Initialize MongoDB collections for development"""
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        db = client["ericDb"]

        # List of collections to create
        collections = [
            "users",
            "news",
            "quality_metrics",
            "generation_logs",
            "tip_sheets",
            "questions",
            "answer_plans",
            "feedback",
            "final_results",
            "nominations",
            "insights",
            "insight_keywords",
            "insight_metadata",
            "topics",
            "settings",
            "articles",
            "trusted_sources",
            "area_preferences",
            "api_keys",
            "french_tips",
            "search_topics",
            "french_blogs",
        ]

        # Create collections
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")

        logger.info("MongoDB initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing MongoDB: {str(e)}")
        raise


if __name__ == "__main__":
    init_mongodb()
