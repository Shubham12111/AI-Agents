import pymongo
from services.logger_service import LoggerUtils, LogLevel

# Initialize Logger
logger = LoggerUtils("MongoDB", LogLevel.DEBUG)

class MongoDB:
    def __init__(self, url, database):
        """
        Initialize MongoDB client using the URI and DB name from the factory module.
        """
        try:
            logger.info("Attempting to connect to MongoDB...")
            self.client = pymongo.MongoClient(url)

            if not database or " " in database:
                raise ValueError(f"Invalid database name: '{database}'")

            self.db = self.client[database]
            logger.info("Connected to MongoDB successfully!")
        except ValueError as ve:
            logger.error(f"Database name error: {ve}")
            self.db = None  # Set to None to prevent crashes
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.db = None  # Prevent crashes

    def insert_one(self, collection_name: str, data: dict):
        """
        Insert a single document into the specified MongoDB collection.
        """
        try:
            collection = self.db[collection_name]
            logger.debug(f"Inserting into {collection_name}: {data}")
            result = collection.insert_one(data)
            logger.info(f"Document inserted with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error("Error inserting document", error=e)
            raise

    def find_one(self, collection_name: str, query: dict):
        """
        Find a single document in the specified MongoDB collection.
        """
        try:
            collection = self.db[collection_name]
            logger.debug(f"Finding one in {collection_name} with query: {query}")
            result = collection.find_one(query)
            logger.info(f"Query result: {result}")
            return result
        except Exception as e:
            logger.error("Error retrieving document", error=e)
            raise

    def fetch_all(self, collection_name: str, query: dict = None, limit: int = 100):
        """
        Fetch multiple documents from the specified MongoDB collection.

        :param collection_name: The name of the collection.
        :param query: MongoDB filter query (default: {} for all documents).
        :param limit: Maximum number of documents to return (default: 100).
        """
        try:
            collection = self.db[collection_name]
            query = query or {}  # Default to fetching all documents
            logger.debug(f"Fetching documents from {collection_name} with query: {query}")
            cursor = collection.find(query).limit(limit)
            results = list(cursor)
            logger.info(f"Fetched {len(results)} documents from {collection_name}.")
            return results
        except Exception as e:
            logger.error("Error fetching documents", error=e)
            raise

    def update_one(self, collection_name: str, query: dict, update_data: dict):
        """
        Update a single document in the specified MongoDB collection.

        :param collection_name: The name of the collection.
        :param query: Filter query to find the document to update.
        :param update_data: The new data to update the document with.
        """
        try:
            collection = self.db[collection_name]
            logger.debug(f"Updating document in {collection_name} with query: {query}, update: {update_data}")
            result = collection.update_one(query, {"$set": update_data})
            logger.info(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
            return result.modified_count
        except Exception as e:
            logger.error("Error updating document", error=e)
            raise

    def delete_one(self, collection_name: str, query: dict):
        """
        Delete a single document from the specified MongoDB collection.

        :param collection_name: The name of the collection.
        :param query: Filter query to find the document to delete.
        """
        try:
            collection = self.db[collection_name]
            logger.debug(f"Deleting from {collection_name} with query: {query}")
            result = collection.delete_one(query)
            logger.info(f"Deleted {result.deleted_count} document(s) from {collection_name}.")
            return result.deleted_count
        except Exception as e:
            logger.error("Error deleting document", error=e)
            raise

    def close_connection(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("MongoDB connection closed.")
        except Exception as e:
            logger.error("Error closing MongoDB connection", error=e)
            raise

