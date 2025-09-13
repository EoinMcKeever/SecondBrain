"""Simplified Todoist integration.

Fetches tasks from Todoist and sends them to Notion, mapping projects to areas
and using labels or title suffixes to set project relations.
"""

import sys
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
from .create_task_notion import NotionTaskCreator
from ..mappings.project_mappings import get_notion_database_id, is_valid_project_mapping

# Load environment variables
load_dotenv()
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")

class TodoistClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {TODOIST_API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.todoist.com/rest/v2"

    def get_tasks(self) -> List[Dict]:
        """Fetch all tasks from Todoist.
        
        Returns: List of task dictionaries from Todoist API
        """
        try:
            response = requests.get(f"{self.base_url}/tasks", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing Todoist API: {e}")
            sys.exit(1)

    def close_task(self, task_id: str) -> bool:
        """Mark a task as complete in Todoist.
        
        Args:
            task_id: The Todoist task ID to close
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            response = requests.post(f"{self.base_url}/tasks/{task_id}/close", headers=self.headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error marking task {task_id} as complete: {e}")
            return False

    def process_task(self, task: Dict) -> Dict:
        """Process a Todoist task, enriching it with area mapping.
        
        Args:
            task: Raw Todoist task dictionary
            
        Returns:
            Dict: Task with area_ids added based on project mapping
        """
        project_id = task.get('project_id')
        if not project_id:
            return task

        # Get corresponding Notion area ID
        area_id = get_notion_database_id(str(project_id))
        if not area_id and not is_valid_project_mapping(str(project_id)):
            print(f"No area mapping for project {project_id}, using inbox")
            area_id = get_notion_database_id('inbox')

        if area_id:
            task['area_ids'] = [area_id]

        return task

def start():
    """Main entry point: fetch Todoist tasks and create them in Notion."""
    print("Fetching your Todoist tasks...")
    
    # Initialize clients
    todoist = TodoistClient()
    notion_creator = NotionTaskCreator()
    
    # Get and process Todoist tasks
    tasks = todoist.get_tasks()
    if not tasks:
        print("No tasks found.")
        return
    
    # Add area mappings and create in Notion
    processed = [todoist.process_task(task) for task in tasks]
    notion_creator.create_tasks(processed)
    
    # Uncomment to enable task closing after creation
    # for task in tasks:
    #    todoist.close_task(task['id'])

