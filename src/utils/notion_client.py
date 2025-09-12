from typing import Dict, List, Optional
import requests
from notion_client import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"

class NotionManager:
    def __init__(self):
        self.client = Client(auth=NOTION_TOKEN)
        self.headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION
        }

    def create_task_in_database(self, database_id: str, properties: Dict) -> Dict:
        """Create a task in the specified Notion database"""
        try:
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"Successfully created task: {properties.get('Name', {}).get('title', [{}])[0].get('text', {}).get('content', 'Unknown')}")
            return response
        except Exception as e:
            print(f"Error creating task in database {database_id}: {str(e)}")
            print(f"Properties that failed: {properties}")
            return None

    def get_database_info(self, database_id: str) -> Dict:
        """Get database information including its properties"""
        try:
            return self.client.databases.retrieve(database_id=database_id)
        except Exception as e:
            print(f"Error retrieving database {database_id}: {str(e)}")
            return None

    def query_database_for_title(self, database_id: str, title: str) -> Optional[Dict]:
        """Query a database for a page whose title equals the given title.
        Returns the page object if found, otherwise None.
        """
        try:
            # Most Notion databases use a 'Name' title property. Query by title equality.
            resp = self.client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Name",
                    "title": {
                        "equals": title
                    }
                }
            )
            results = resp.get('results', [])
            return results[0] if results else None
        except Exception as e:
            print(f"Error querying database {database_id} for title '{title}': {e}")
            return None

    def find_or_create_page_in_database(self, database_id: str, title: str) -> Optional[str]:
        """Find a page in a database by title or create it. Returns the page id."""
        page = self.query_database_for_title(database_id, title)
        if page:
            return page.get('id')

        # Create a new page in the database with the given title
        try:
            new_page = self.client.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Name": {"title": [{"text": {"content": title}}]}
                }
            )
            return new_page.get('id')
        except Exception as e:
            print(f"Error creating page '{title}' in database {database_id}: {e}")
            return None

    def create_page_under_page(self, parent_page_id: str, title: str, body: str = None) -> Optional[str]:
        """Create a simple child page under an existing page. Returns the new page id or None."""
        try:
            children = []
            # Add a heading block for the title
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": title}}]}
            })
            if body:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": body}}]}
                })

            page = self.client.pages.create(
                parent={"page_id": parent_page_id},
                children=children
            )
            return page.get('id')
        except Exception as e:
            print(f"Error creating child page under page {parent_page_id}: {e}")
            return None
