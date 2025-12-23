"""
Orchestration Tools - MCP Tool Wrappers

18 tools for Nova Orchestration:
- Config (6): list_prompts, update_prompt, activate_prompt, list_mcp_configs, update_mcp_config, get_active
- Objective (5): define, check, achieve_checkpoint, record_iteration, fail
- Loop (4): configure, iterate, stop, status
- Safe Point (3): create, rollback, list

Note: Agent tools (route, spawn, status) removed - Claude Code native Task tool with
subagent_type now provides equivalent functionality.
"""

from .config_list_prompts import config_list_prompts
from .config_update_prompt import config_update_prompt
from .config_activate_prompt import config_activate_prompt
from .config_list_mcp_configs import config_list_mcp_configs
from .config_update_mcp_config import config_update_mcp_config
from .config_get_active import config_get_active
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
    # Config (Phase 6)
    "config_list_prompts",
    "config_update_prompt",
    "config_activate_prompt",
    "config_list_mcp_configs",
    "config_update_mcp_config",
    "config_get_active",
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
