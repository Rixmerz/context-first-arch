"""
MCP Tool: workflow.onboard

Generate initial project context for AI-assisted development.
"""

from typing import Any, Dict

from src.core.workflow.onboarding import generate_onboarding


async def workflow_onboard(
    project_path: str,
    include_contracts: bool = True,
    include_decisions: bool = True,
    max_context_size: int = 50000
) -> Dict[str, Any]:
    """
    Generate comprehensive project context for AI onboarding.

    Collects and structures essential project information including
    project map, settings, current task, decisions, and contracts
    to provide full context for AI-assisted development.

    Args:
        project_path: Path to the project root
        include_contracts: Include contract summaries (default: True)
        include_decisions: Include architecture decisions (default: True)
        max_context_size: Maximum context size in characters (default: 50000)

    Returns:
        Dictionary with:
            - success: Boolean
            - project_name: Name of the project
            - cfa_version: CFA version used
            - context: Full onboarding context
            - context_size: Size of context in characters
            - files_read: List of files included in context
            - truncated: Whether context was truncated

    Example:
        # Full onboarding
        result = await workflow_onboard(
            project_path="/projects/my-app"
        )

        # Lightweight onboarding (faster)
        result = await workflow_onboard(
            project_path="/projects/my-app",
            include_contracts=False,
            include_decisions=False,
            max_context_size=20000
        )

    Best Practice:
        Run this at the start of each development session to ensure
        the AI has full project context. The context includes:
        - Project structure and conventions
        - Current task and progress
        - Architecture decisions
        - Contract boundaries

    After onboarding, use workflow.check_onboard to verify status.
    """
    try:
        result = generate_onboarding(
            project_path=project_path,
            include_contracts=include_contracts,
            include_decisions=include_decisions,
            max_context_size=max_context_size
        )

        return result

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"Project not found: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Onboarding failed: {str(e)}"
        }
