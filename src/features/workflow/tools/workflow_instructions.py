"""
MCP Tool: workflow.instructions

Get initial instructions for CFA development workflow.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.project import get_project_paths


async def workflow_instructions(project_path: str) -> Dict[str, Any]:
    """
    Get initial instructions for Context-First Architecture workflow.

    Returns comprehensive guidance for AI-assisted development
    using the CFA methodology, including workflow steps,
    best practices, and tool recommendations.

    Args:
        project_path: Path to the project root

    Returns:
        Dictionary with:
            - success: Boolean
            - project_detected: Whether a CFA project was found
            - cfa_version: Detected CFA version
            - workflow_steps: Ordered workflow steps
            - tool_recommendations: When to use each tool
            - best_practices: Key practices to follow

    Example:
        # At session start
        result = await workflow_instructions(
            project_path="/projects/my-app"
        )

        # Follow the workflow steps
        for step in result["workflow_steps"]:
            print(f"{step['order']}. {step['name']}: {step['description']}")

    Purpose:
        This tool provides a complete reference for the CFA workflow.
        Use it when:
        - Starting a new development session
        - Onboarding to a new project
        - Refreshing on CFA methodology
        - Training or explaining the workflow
    """
    try:
        paths = get_project_paths(project_path)
        root = paths["root"]

        # Detect CFA project
        is_cfa_project = (paths["claude_dir"]).exists()

        # Detect version
        cfa_version = "unknown"
        if is_cfa_project:
            settings_file = paths["claude_dir"] / "settings.json"
            if settings_file.exists():
                import json
                try:
                    settings = json.loads(settings_file.read_text())
                    cfa_version = settings.get("cfa_version", "1.0")
                except json.JSONDecodeError:
                    pass

        # Workflow steps
        workflow_steps = [
            {
                "order": 1,
                "name": "Onboard",
                "tool": "workflow.onboard",
                "description": "Load project context at session start",
                "when": "Beginning of every session"
            },
            {
                "order": 2,
                "name": "Understand Task",
                "tool": "task.start",
                "description": "Record and analyze the task requirements",
                "when": "When given a new task"
            },
            {
                "order": 3,
                "name": "Gather Information",
                "tool": "symbol.find, file.read",
                "description": "Explore codebase to understand context",
                "when": "Before implementation"
            },
            {
                "order": 4,
                "name": "Reflect on Information",
                "tool": "workflow.think_info",
                "description": "Analyze gathered information systematically",
                "when": "After exploration, before planning"
            },
            {
                "order": 5,
                "name": "Plan Approach",
                "tool": "workflow.think_task",
                "description": "Validate approach against requirements",
                "when": "Before starting implementation"
            },
            {
                "order": 6,
                "name": "Implement",
                "tool": "symbol.replace, file.create",
                "description": "Make changes following the plan",
                "when": "During implementation"
            },
            {
                "order": 7,
                "name": "Validate Completion",
                "tool": "workflow.think_done",
                "description": "Verify all requirements are met",
                "when": "Before marking task complete"
            },
            {
                "order": 8,
                "name": "Summarize",
                "tool": "workflow.summarize",
                "description": "Generate change summary for documentation",
                "when": "After completing work"
            },
            {
                "order": 9,
                "name": "Complete Task",
                "tool": "task.complete",
                "description": "Mark task as done and update records",
                "when": "After validation passes"
            }
        ]

        # Tool recommendations by category
        tool_recommendations = {
            "context_loading": [
                "workflow.onboard - Full project context",
                "workflow.check_onboard - Verify context freshness",
                "context.load - Load specific context files"
            ],
            "task_management": [
                "task.start - Begin new task",
                "task.update - Record progress",
                "task.complete - Finish task"
            ],
            "code_exploration": [
                "symbol.find - Find symbols by name",
                "symbol.overview - Get file structure",
                "symbol.references - Find usages",
                "file.search - Search for patterns"
            ],
            "code_modification": [
                "symbol.replace - Replace implementation",
                "symbol.rename - Rename across project",
                "file.create - Create new files",
                "file.replace - Search and replace"
            ],
            "reflection": [
                "workflow.think_info - Analyze information",
                "workflow.think_task - Validate approach",
                "workflow.think_done - Verify completion"
            ],
            "documentation": [
                "workflow.summarize - Generate summaries",
                "decision.add - Record decisions",
                "contract.create - Define contracts"
            ]
        }

        # Best practices
        best_practices = [
            "Always onboard at session start to load full context",
            "Use contracts to define boundaries before implementation",
            "Validate approach with workflow.think_task before coding",
            "Use symbol tools for semantic code changes",
            "Reflect on information before making decisions",
            "Verify completion with workflow.think_done checklist",
            "Summarize changes for documentation and commits",
            "Update decisions.md for significant choices",
            "Keep current-task.md updated for continuity"
        ]

        return {
            "success": True,
            "project_path": str(root),
            "project_detected": is_cfa_project,
            "cfa_version": cfa_version,
            "workflow_steps": workflow_steps,
            "tool_recommendations": tool_recommendations,
            "best_practices": best_practices,
            "quick_start": (
                "1. Run workflow.onboard to load context\n"
                "2. Run task.start to begin your task\n"
                "3. Use symbol.* tools for code exploration\n"
                "4. Use workflow.think_* for reflection\n"
                "5. Run workflow.think_done before completing"
            )
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get instructions: {str(e)}"
        }
