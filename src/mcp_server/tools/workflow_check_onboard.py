"""
MCP Tool: workflow.check_onboard

Check if onboarding has been performed and if refresh is needed.
"""

from typing import Any, Dict

from src.core.workflow.onboarding import check_onboarding_status


async def workflow_check_onboard(project_path: str) -> Dict[str, Any]:
    """
    Check onboarding status for current session.

    Verifies whether onboarding has been performed and whether
    the context might be stale due to file changes.

    Args:
        project_path: Path to the project root

    Returns:
        Dictionary with:
            - success: Boolean
            - onboarded: Whether onboarding was performed
            - last_onboarding: Timestamp of last onboarding
            - hours_ago: Hours since last onboarding
            - files_changed_since: Files that changed since onboarding
            - needs_refresh: Whether refresh is recommended
            - recommendation: Action recommendation

    Example:
        # Check status at session start
        result = await workflow_check_onboard(
            project_path="/projects/my-app"
        )

        if not result["onboarded"] or result["needs_refresh"]:
            # Run onboarding
            await workflow_onboard(project_path="/projects/my-app")

    Best Practice:
        Check onboarding status at the start of each session and
        after significant file changes to ensure context is current.
    """
    try:
        result = check_onboarding_status(project_path=project_path)

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check onboarding status: {str(e)}"
        }
