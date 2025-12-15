"""
MCP Tool: agent.route

Haiku-based task routing - analyzes task and decides which model should handle it.
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.orchestration import TaskRouter, ModelType


# Cache global para reutilizar routers
_routers: Dict[str, TaskRouter] = {}


def _get_router() -> TaskRouter:
    """
    Get or create TaskRouter instance.

    Returns:
        TaskRouter instance
    """
    key = "default"
    if key not in _routers:
        _routers[key] = TaskRouter()
    return _routers[key]


async def agent_route(
    task: str,
    context: Optional[str] = None,
    project_path: Optional[str] = None,
    force_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a task and route it to the appropriate model.

    Uses Haiku-style local analysis to determine task complexity
    and route to the optimal model (Haiku, Sonnet, or Opus).

    Args:
        task: The task description to analyze
        context: Optional context about the project/codebase
        project_path: Optional path to CFA project for enriched analysis
        force_model: Optional override to force a specific model

    Returns:
        Dictionary with:
            - analysis: Task analysis (complexity, type, etc.)
            - decision: Recommended model (haiku/sonnet/opus)
            - reasoning: Explanation of the decision
            - model_info: Information about the selected model

    Example:
        result = await agent_route(
            task="Refactor the authentication module to use JWT",
            context="Using Express.js backend with MongoDB"
        )
        # Returns: {"decision": "sonnet", "reasoning": "..."}
    """
    try:
        # Get router
        router = _get_router()

        # Convert string model to ModelType if forced
        force_model_type = None
        if force_model:
            model_map = {
                "haiku": ModelType.HAIKU,
                "sonnet": ModelType.SONNET,
                "opus": ModelType.OPUS
            }
            force_model_type = model_map.get(force_model.lower())

            if not force_model_type:
                return {
                    "success": False,
                    "error": f"Invalid model: {force_model}. Valid models: haiku, sonnet, opus"
                }

        # Delegate to core router
        routing_decision = router.route_task(
            task=task,
            context=context,
            force_model=force_model_type
        )

        # Get escalation path
        escalation_path = router.get_escalation_path(routing_decision.recommended_model)

        # Build response
        return {
            "success": True,
            "analysis": {
                "complexity": routing_decision.analysis.complexity.value,
                "estimated_lines": routing_decision.analysis.estimated_lines,
                "requires_planning": routing_decision.analysis.requires_planning,
                "multi_file": routing_decision.analysis.multi_file,
                "type": routing_decision.analysis.task_type
            },
            "decision": routing_decision.recommended_model.value,
            "reasoning": routing_decision.reasoning,
            "confidence": routing_decision.confidence,
            "model_info": {
                "strengths": ["fast", "routing", "simple tasks", "coordination"]
                if routing_decision.recommended_model == ModelType.HAIKU
                else ["implementation", "debugging", "refactoring", "tests"]
                if routing_decision.recommended_model == ModelType.SONNET
                else ["architecture", "planning", "complex reasoning", "design"],
                "cost_multiplier": 1.0 if routing_decision.recommended_model == ModelType.HAIKU
                else 5.0 if routing_decision.recommended_model == ModelType.SONNET
                else 15.0
            },
            "all_models": ["haiku", "sonnet", "opus"],
            "escalation_path": escalation_path.value if escalation_path else None,
            "forced": force_model is not None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Routing failed: {str(e)}",
            "fallback_decision": "sonnet",
            "fallback_reasoning": "Using Sonnet as safe default due to analysis error"
        }
