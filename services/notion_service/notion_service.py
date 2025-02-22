import requests
import json
from services.logger_service import LoggerUtils, LogLevel

# Initialize Logger
logger = LoggerUtils("NotionAPI", LogLevel.DEBUG)

class NotionAPI:
    """Helper class to interact with Notion API and store blog posts."""

    def __init__(self, api, database, url):
        """Initialize Notion API with authentication headers."""
        self.headers = {
            "Authorization": f"Bearer {api}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",  # Update to latest Notion API version
        }
        self.database_id = database
        self.api_url = f"{url}/v1/pages"

    def create_blog_page(self, title: str, content: str, tags: list = None): 
        """
        Create a new blog post page in Notion.

        :param title: The title of the blog post.
        :param content: The content/body of the blog post.
        :param tags: List of tags for categorization (Optional).
        :return: Notion page ID if successful, None otherwise.
        """
        tags = tags or []
        notion_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": title}}]
                },
                "Tags": {
                    "multi_select": [{"name": tag} for tag in tags]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": content}}]
                    }
                }
            ]
        }

        try:
            logger.info(f"Creating Notion page for blog: {title}")
            response = requests.post(self.api_url, headers=self.headers, json=notion_data)
            response_data = response.json()

            if response.status_code == 200:
                notion_page_id = response_data.get("id")
                logger.info(f"Blog post created successfully! Notion Page ID: {notion_page_id}")
                return notion_page_id
            else:
                logger.error(f"Failed to create blog post: {response_data}")
                return None

        except Exception as e:
            logger.error("Error while creating Notion page", error=e)
            return None

