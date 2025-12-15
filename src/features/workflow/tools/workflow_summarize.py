"""
MCP Tool: workflow.summarize

Generate structured summary of changes made.
"""

from typing import Any, Dict, List, Optional

from src.features.workflow.core.reflection import summarize_changes


async def workflow_summarize(
    project_path: str,
    changes: List[Dict[str, str]],
    task_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a structured summary of changes made.

    Creates comprehensive change summaries suitable for
    commit messages, PR descriptions, or documentation.

    Args:
        project_path: Path to the project root
        changes: List of changes, each with:
                 - file: File path
                 - type: "added", "modified", or "deleted"
                 - description: What was changed
        task_description: Optional task context for the summary

    Returns:
        Dictionary with:
            - success: Boolean
            - changes_count: Total number of changes
            - files_added: Count of new files
            - files_modified: Count of modified files
            - files_deleted: Count of deleted files
            - summary: Formatted change summary
            - commit_message_suggestion: Suggested commit message
            - guidance: How to use the summary

    Example:
        # After completing a feature
        result = await workflow_summarize(
            project_path="/projects/my-app",
            changes=[
                {
                    "file": "src/auth/middleware.py",
                    "type": "added",
                    "description": "JWT authentication middleware"
                },
                {
                    "file": "src/routes/auth.py",
                    "type": "added",
                    "description": "Login and logout endpoints"
                },
                {
                    "file": "src/config.py",
                    "type": "modified",
                    "description": "Added JWT secret configuration"
                }
            ],
            task_description="Implement JWT authentication system"
        )

        # Use the commit message suggestion
        print(result["commit_message_suggestion"])
        # Output: "Implement JWT authentication system"

    Best Practice:
        Use this tool after completing work to generate consistent,
        well-structured change documentation. The summary can be used for:
        - Git commit messages
        - Pull request descriptions
        - Changelog entries
        - Team updates
    """
    try:
        result = summarize_changes(
            project_path=project_path,
            changes=changes,
            task_description=task_description
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Summarization failed: {str(e)}"
        }
