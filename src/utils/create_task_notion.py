"""Simplified Notion task creator.

Only creates a database entry with these properties:
 - Name (from task content)
 - Date (due date)
 - Description
 - Project relation (from first label or title suffix ' @Project')
 - Areas relation (from provided area IDs)

This file intentionally omits logging, resources, notes, and other features.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import os

from .notion_client import NotionManager
from .project_mappings import get_notion_database_id


@dataclass
class TaskProperties:
    title: str
    date: Optional[str] = None
    description: Optional[str] = None
    project_name: Optional[str] = None
    area_ids: Optional[List[str]] = None
    priority: Optional[int] = None  # Todoist priority: 4 (urgent) to 1 (low)


class TodoistTaskConverter:
    @staticmethod
    def extract_project_from_title(title: str) -> Tuple[str, Optional[str]]:
        parts = title.split(' @')
        return (parts[0].strip(), parts[1].strip()) if len(parts) > 1 else (title.strip(), None)

    @staticmethod
    def get_due_date(due_info: Dict) -> Optional[str]:
        if not due_info:
            return None
        return due_info.get('datetime') or due_info.get('date')

    @staticmethod
    def convert_to_notion_task(todoist_task: dict) -> TaskProperties:
        title, project_from_title = TodoistTaskConverter.extract_project_from_title(
            todoist_task.get('content', '')
        )

        due_date = TodoistTaskConverter.get_due_date(todoist_task.get('due', {}))
        labels = todoist_task.get('labels', []) or []
        project_name = project_from_title or (labels[0] if labels else None)

        # area IDs may be passed via a custom field or mapping; prefer mapping from Todoist project
        # Try common Todoist project id keys
        project_id = todoist_task.get('project_id') or todoist_task.get('project')
        mapped_area = get_notion_database_id(str(project_id)) if project_id else None
        area_ids = [mapped_area] if mapped_area else (todoist_task.get('area_ids') or None)

        # Map Todoist priority (4=urgent to 1=low) to a text label
        priority = todoist_task.get('priority', 1)  # Default to 1 (low) if not set
        
        return TaskProperties(
            title=title,
            date=due_date,
            description=todoist_task.get('description'),
            project_name=project_name,
            area_ids=area_ids,
            priority=priority
        )


class NotionPropertyBuilder:
    @staticmethod
    def build_properties(task: TaskProperties) -> dict:
        props = {
            "Name": {"title": [{"text": {"content": task.title}}]}
        }

        if task.date:
            props["Date"] = {"date": {"start": task.date}}

        if task.description:
            props["Description"] = {"rich_text": [{"text": {"content": task.description}}]}

        # Areas relation (accept multiple area ids)
        if task.area_ids:
            props["Areas"] = {"relation": [{"id": a} for a in task.area_ids if a]}

        # Priority as a select field (Todoist: 4=urgent to 1=low)
        if task.priority:
            priority_map = {
                4: "Urgent",
                3: "High",
                2: "Medium",
                1: "Low"
            }
            priority_text = priority_map.get(task.priority, "Low")
            props["Priority"] = {"select": {"name": priority_text}}

        return props


class NotionTaskCreator:
    def __init__(self, notion_client: Optional[NotionManager] = None):
        self.notion_client = notion_client or NotionManager()

    def create_tasks(self, todoist_tasks: List[dict], tasks_db_id: Optional[str] = None) -> List[dict]:
        """Create minimal task entries in the Notion tasks database.

        todoist_tasks: list of raw Todoist task dicts
        tasks_db_id: optional override; defaults to NOTION_TASKS_DB env var
        """
        created = []
        tasks_db_id = tasks_db_id or os.getenv('NOTION_TASKS_DB')
        if not tasks_db_id:
            raise RuntimeError('NOTION_TASKS_DB not set')

        # Try to read DB schema once to detect a project relation property
        project_prop = None
        project_target_db = None
        try:
            db_info = self.notion_client.get_database_info(tasks_db_id)
            props = db_info.get('properties', {}) if isinstance(db_info, dict) else {}
            # prefer a property with "project" in the name
            for name, meta in props.items():
                if meta.get('type') == 'relation' and 'project' in name.lower():
                    project_prop = name
                    project_target_db = meta.get('relation', {}).get('database_id')
                    break
            # fallback: first relation property
            if not project_prop:
                for name, meta in props.items():
                    if meta.get('type') == 'relation':
                        project_prop = name
                        project_target_db = meta.get('relation', {}).get('database_id')
                        break
        except Exception:
            project_prop = None
            project_target_db = None

        for raw in todoist_tasks:
            try:
                t = TodoistTaskConverter.convert_to_notion_task(raw)
                properties = NotionPropertyBuilder.build_properties(t)

                # Project relation: create or find the project page in the target DB
                if t.project_name and project_prop and project_target_db:
                    try:
                        project_page_id = self.notion_client.find_or_create_page_in_database(project_target_db, t.project_name)
                        if project_page_id:
                            properties[project_prop] = {"relation": [{"id": project_page_id}]}
                    except Exception:
                        # ignore project linking failures and continue creating the task
                        pass

                created_page = self.notion_client.create_task_in_database(database_id=tasks_db_id, properties=properties)
                if created_page:
                    created.append(created_page)
            except Exception as e:
                print(f"Failed to create task from Todoist entry: {e}")

        return created

