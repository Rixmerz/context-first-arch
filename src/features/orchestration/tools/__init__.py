"""
Orchestration Tools - MCP Tool Wrappers

15 tools for Nova Agent Orchestration:
- Agent (3): route, spawn, status
- Objective (5): define, check, achieve_checkpoint, record_iteration, fail
- Loop (4): configure, iterate, stop, status
- Safe Point (3): create, rollback, list
"""

from .agent_route import agent_route
from .agent_spawn import agent_spawn
from .agent_status import agent_status
from .objective_define import objective_define
from .objective_check import objective_check
from .objective_achieve_checkpoint import objective_achieve_checkpoint
from .objective_record_iteration import objective_record_iteration
from .objective_fail import objective_fail
from .loop_configure import loop_configure
from .loop_iterate import loop_iterate
from .loop_stop import loop_stop
from .loop_status import loop_status
from .safe_point_create import safe_point_create
from .safe_point_rollback import safe_point_rollback
from .safe_point_list import safe_point_list

__all__ = [
    # Agent
    "agent_route",
    "agent_spawn",
    "agent_status",
    # Objective
    "objective_define",
    "objective_check",
    "objective_achieve_checkpoint",
    "objective_record_iteration",
    "objective_fail",
    # Loop
    "loop_configure",
    "loop_iterate",
    "loop_stop",
    "loop_status",
    # Safe Point
    "safe_point_create",
    "safe_point_rollback",
    "safe_point_list",
]
