"""
MCP Tool: workflow.reflect

Consolidated reflection tool for structured AI thinking.
Combines: think_info, think_task, think_done
"""

from typing import Any, Dict, List, Optional, Literal

from src.features.workflow.core.reflection import (
    think_about_information,
    think_about_task,
    think_about_completion
)


async def workflow_reflect(
    project_path: str,
    reflect_type: Literal["info", "task", "done"],
    content: str,
    context: Optional[str] = None,
    # Type-specific parameters
    questions: Optional[List[str]] = None,      # for "info"
    concerns: Optional[List[str]] = None,       # for "task"
    tests_passed: bool = False                  # for "done"
) -> Dict[str, Any]:
    """
    [PRIMARY] Structured reflection for AI meta-cognition.

    Provides templates and checklists for different reflection stages:
    - "info": Analyze gathered information before proceeding
    - "task": Validate approach against requirements before coding
    - "done": Verify completion before marking task finished

    Args:
        project_path: Path to the project root
        reflect_type: Type of reflection - "info", "task", or "done"
        content: Main content to reflect on:
            - For "info": Information gathered
            - For "task": Current implementation approach
            - For "done": Summary of work completed
        context: Additional context (optional)
            - For "info": Background context
            - For "task": Task description
            - For "done": Original task description
        questions: Specific questions to consider (for "info" type)
        concerns: Concerns to address (for "task" type)
        tests_passed: Whether tests passed (for "done" type)

    Returns:
        Dictionary with reflection template and guidance specific to type.

    Examples:
        # After gathering information
        result = await workflow_reflect(
            project_path=".",
            reflect_type="info",
            content="Found JWT auth pattern, REST conventions...",
            questions=["Is there existing middleware?"]
        )

        # Before implementing
        result = await workflow_reflect(
            project_path=".",
            reflect_type="task",
            content="Plan: 1) Add auth middleware 2) Create endpoints",
            context="Task: Add user authentication"
        )

        # Before marking complete
        result = await workflow_reflect(
            project_path=".",
            reflect_type="done",
            content="Implemented login, logout, auth middleware",
            context="Original task: Add user authentication",
            tests_passed=True
        )

    Best Practice:
        Use "info" after gathering context, "task" before coding,
        "done" before completing. This ensures thorough thinking
        at each stage.
    """
    try:
        if reflect_type == "info":
            result = think_about_information(
                project_path=project_path,
                information=content,
                context=context,
                questions=questions
            )
        elif reflect_type == "task":
            # For task type, context is the task description
            result = think_about_task(
                project_path=project_path,
                task_description=context or "Task not specified",
                current_approach=content,
                concerns=concerns
            )
        elif reflect_type == "done":
            # For done type, context is the original task description
            result = think_about_completion(
                project_path=project_path,
                task_description=context or "Task not specified",
                work_done=content,
                tests_passed=tests_passed
            )
        else:
            return {
                "success": False,
                "error": f"Unknown reflect_type: {reflect_type}. Use 'info', 'task', or 'done'"
            }

        # Add reflect_type to result for clarity
        result["reflect_type"] = reflect_type
        return result

    except Exception as e:
        return {
            "success": False,
            "reflect_type": reflect_type,
            "error": f"Reflection failed: {str(e)}"
        }
