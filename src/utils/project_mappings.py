from typing import Dict, Optional
from .notion_codes import (
    PERSONAL_AREA_ID, 
    ACUMIS_AREA_ID, 
    FITTNESS_AREA_ID,
    NUTRITION_AREA_ID,
    FIND_JOB_AREA_ID,
    INVESTING_AREA_ID,
    NEW_PROJECTS_ID,
    ACUMIS_TODOIST_ID,
    PERSONAL_TODOIST_ID
)

# Mapping of Todoist project IDs to Notion database IDs
PROJECT_MAPPINGS = {
    # Main areas
    PERSONAL_TODOIST_ID: PERSONAL_AREA_ID,     # Personal
    ACUMIS_TODOIST_ID: ACUMIS_AREA_ID,         # Work/Acumis
    
    # Additional areas (commented out in notion_codes.py)
    # "2359488880": FITTNESS_AREA_ID,          # Fitness
    # "2359488881": NUTRITION_AREA_ID,         # Nutrition
    # "2359488882": FIND_JOB_AREA_ID,         # Find Job
    # "2359488883": INVESTING_AREA_ID,         # Investing
    
    # Default/Inbox
    "inbox": NEW_PROJECTS_ID                    # Default for uncategorized tasks
}

def get_notion_database_id(todoist_project_id: str) -> Optional[str]:
    """
    Get the corresponding Notion database ID for a Todoist project ID.
    Returns None if no mapping exists.
    """
    return PROJECT_MAPPINGS.get(str(todoist_project_id))

def is_valid_project_mapping(todoist_project_id: str) -> bool:
    """
    Check if a valid mapping exists for the given Todoist project ID.
    """
    notion_id = get_notion_database_id(todoist_project_id)
    return notion_id is not None and notion_id != ""
