"""
MCP Tool: workflow.onboard

[START HERE] Generate initial project context for AI-assisted development.
Consolidates: onboard + check_onboard
"""

from typing import Any, Dict

from src.core.workflow.onboarding import generate_onboarding, check_onboarding_status


async def workflow_onboard(
    project_path: str,
    check_only: bool = False,
    include_contracts: bool = True,
    include_decisions: bool = True,
    max_context_size: int = 50000
) -> Dict[str, Any]:
    """
    [START HERE] Load full project context for new sessions.

    Primary entry point for AI-assisted development. Either loads
    complete project context or checks if refresh is needed.

    Args:
        project_path: Path to the project root
        check_only: If True, only check status without full onboarding
        include_contracts: Include contract summaries (default: True)
        include_decisions: Include architecture decisions (default: True)
        max_context_size: Maximum context size in characters (default: 50000)

    Returns:
        When check_only=False (default):
            - success: Boolean
            - project_name: Name of the project
            - cfa_version: CFA version used
            - context: Full onboarding context
            - context_size: Size of context in characters
            - files_read: List of files included in context
            - truncated: Whether context was truncated

        When check_only=True:
            - success: Boolean
            - onboarded: Whether onboarding was performed
            - last_onboarding: Timestamp of last onboarding
            - hours_ago: Hours since last onboarding
            - files_changed_since: Files changed since onboarding
            - needs_refresh: Whether refresh is recommended
            - recommendation: Action recommendation

    Examples:
        # Full onboarding (typical session start)
        result = await workflow_onboard(project_path="/projects/my-app")

        # Quick status check
        status = await workflow_onboard(
            project_path="/projects/my-app",
            check_only=True
        )
        if status["needs_refresh"]:
            result = await workflow_onboard(project_path="/projects/my-app")

        # Lightweight onboarding (faster, less context)
        result = await workflow_onboard(
            project_path="/projects/my-app",
            include_contracts=False,
            include_decisions=False,
            max_context_size=20000
        )

    Best Practice:
        ALWAYS run this at session start. The context includes:
        - Project structure and conventions
        - Current task and progress
        - Architecture decisions
        - Contract boundaries

        Use check_only=True to verify if re-onboarding is needed
        after significant file changes.
    """
    try:
        if check_only:
            # Check status only
            result = check_onboarding_status(project_path=project_path)
            result["mode"] = "check"
        else:
            # Full onboarding
            result = generate_onboarding(
                project_path=project_path,
                include_contracts=include_contracts,
                include_decisions=include_decisions,
                max_context_size=max_context_size
            )
            result["mode"] = "full"

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "mode": "check" if check_only else "full",
            "error": f"Project not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "mode": "check" if check_only else "full",
            "error": f"Onboarding failed: {str(e)}"
        }
