from google.cloud import secretmanager
from google.oauth2 import service_account
import json
import os
from services.logger_service import LoggerUtils, LogLevel
from fastapi import HTTPException
from dotenv import load_dotenv  # Importing dotenv to load .env file

from openai import OpenAI
from services.mongo_service.mongo_service import MongoDB
from services.notion_service.notion_service import NotionAPI

# Initialize the logger
logger = LoggerUtils("factory", LogLevel.DEBUG)

# Load environment variables from .env file first
load_dotenv()

# # Initialize Services directly from environment variables
# OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# MONGO_SERVICE = MongoDB(
#     url=os.getenv("MONGODB_URI"), database=os.getenv("MONGODB_DB_NAME")
# )

# NOTION_SERVICE = NotionAPI(
#     api=os.getenv("NOTION_API_TOKEN", "Not Found"),
#     database=os.getenv("NOTION_DATABASE_ID", "Not Found"),
#     url=os.getenv("NOTION_API_URL", "Not Found"),
# )

# # Log the configuration being used
# logger.info(f"CUSTOM_SEARCH_API: {os.getenv('CUSTOM_SEARCH_API')}")
# logger.info(f"MONGODB_URI: {os.getenv('MONGODB_URI')}")
# logger.info(f"OPEN_API_KEY: {os.getenv('OPEN_API_KEY')}")


class SecretManager:
    """GCP Secret Manager helper class to fetch secrets."""

    def __init__(self, project_id):
        """
        Initialize the SecretManager client.

        :param project_id: GCP Project ID
        """
        # Load Service Account Credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            "ai-press-capmad-2dcf8973ff1a.json"
        )
        self.client = secretmanager.SecretManagerServiceClient(
            credentials=self.credentials
        )
        self.project_id = project_id

    def list_secrets(self):
        """
        List all secret names stored in GCP Secret Manager.

        :return: List of secret names
        """
        try:
            parent = f"projects/{self.project_id}"
            secrets = [
                secret.name.split("/")[-1]
                for secret in self.client.list_secrets(request={"parent": parent})
            ]
            return secrets
        except Exception as e:
            logger.error(f"Error listing secrets from GCP Secret Manager: {str(e)}")
            return []

    def get_secret(self, secret_name):
        """
        Retrieve a secret from GCP Secret Manager.

        :param secret_name: Name of the secret in Secret Manager
        :return: Secret value as a dictionary (if stored in JSON format)
        """
        secret_path = (
            f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
        )

        try:
            response = self.client.access_secret_version(name=secret_path)
            secret_value = response.payload.data.decode("UTF-8")

            # Try to parse as JSON, otherwise return as string
            try:
                return json.loads(secret_value)
            except json.JSONDecodeError:
                return secret_value

        except Exception as e:
            logger.error(
                f"Error retrieving secret '{secret_name}' from GCP Secret Manager: {str(e)}"
            )
            return None  # Return None if retrieval fails


# Example usage
try:
    project_id = "ai-press-capmad"  # Replace with actual GCP project ID

    # Initialize SecretManager
    secret_manager = SecretManager(project_id)

    # Get a list of all secret keys
    secret_keys = secret_manager.list_secrets()
    print("From GCP Secrets ------------------->", secret_keys)

    # Dictionary to store retrieved secrets
    secrets = {}

    # Retrieve all secret values
    for secret_name in secret_keys:
        secret_value = secret_manager.get_secret(secret_name)
        secrets[secret_name] = secret_value
    print("From GCP Secrets ------------------->", secrets)
    # If secrets are not found in Secret Manager, fallback to .env file
    if not secrets:
        logger.info(
            "Secrets not found in GCP Secret Manager, falling back to .env file."
        )
        secrets = {
            "OPEN_API_KEY": os.getenv("OPEN_API_KEY", "Not Found"),
            "MONGODB_URI": "mongodb://localhost:27017",  # Local MongoDB URI
            "MONGODB_DB_NAME": "ericDb",  # Local database name
            "MONGODB_COLLECTION_NAME": os.getenv(
                "MONGODB_COLLECTION_NAME", "Not Found"
            ),
            "CUSTOM_SEARCH_API": os.getenv("CUSTOM_SEARCH_API", "Not Found"),
            "CUSTOM_SEARCH_ID": os.getenv("CUSTOM_SEARCH_ID", "Not Found"),
            "NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN", "Not Found"),
            "NOTION_DATABASE_ID": os.getenv("NOTION_DATABASE_ID", "Not Found"),
            "NOTION_API_URL": os.getenv("NOTION_API_URL", "Not Found"),
        }

    # Override secrets with environment variables if they exist
    for key in secrets:
        env_value = os.getenv(key)
        if env_value is not None:
            secrets[key] = env_value

    # Log retrieved secrets
    # for key, value in secrets.items():
    #     logger.info(f"{key}: {value}")

except Exception as e:
    logger.error(f"Error in secret retrieval: {str(e)}")
    # Fallback to local configuration if secret retrieval fails
    secrets = {
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB_NAME": "ericDb",
        "OPEN_API_KEY": os.getenv("OPEN_API_KEY") or os.getenv("OPENAI_API_KEY"),
    }

# Initialize Services using the final configuration
api_key = (
    secrets.get("OPEN_API_KEY")
    or os.getenv("OPEN_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)

if not api_key:
    raise ValueError("OpenAI API key not found in secrets or environment variables")

OPENAI_CLIENT = OpenAI(api_key=api_key)

# Always use local MongoDB for development
MONGO_SERVICE = MongoDB(
    url="mongodb://localhost:27017",
    database="ericDb",
)

NOTION_SERVICE = NotionAPI(
    api=secrets.get("NOTION_API_TOKEN", os.getenv("NOTION_API_TOKEN", "Not Found")),
    database=secrets.get(
        "NOTION_DATABASE_ID", os.getenv("NOTION_DATABASE_ID", "Not Found")
    ),
    url=secrets.get("NOTION_API_URL", os.getenv("NOTION_API_URL", "Not Found")),
)

# Export the client
__all__ = ["OPENAI_CLIENT"]
