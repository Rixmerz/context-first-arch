"""MCP Tools for Context-First Architecture v3 - Feature-Based Architecture.

74 tools total organized by feature:
- Project/Task/Context/Decision (9): CFA core management
- Memory (5): Persistent project knowledge
- Orchestration (15): Nova multi-model AI orchestration
- Knowledge Graph (12): Intelligent context retrieval
- Symbol (8): Semantic code operations via LSP
- File (7): Enhanced file operations
- Contract (4): Contract management
- Workflow (4): Meta-cognition and reflection
- Analysis (4): Code analysis and metrics
- Timeline (4): Snapshot management and rollback
- Rules (4): Business rules capture

All features follow CFA v2 architecture: features/{name}/core + features/{name}/tools
"""

# =============================================================================
# CFA Core Tools (stay in mcp_server/tools - infrastructure, not features)
# =============================================================================

# Project Tools
from src.mcp_server.tools.project_init import project_init
from src.mcp_server.tools.project_scan import project_scan
from src.mcp_server.tools.project_migrate import project_migrate

# Context Tools
from src.mcp_server.tools.context_load import context_load
from src.mcp_server.tools.context_optimize import context_optimize

# Task Tools
from src.mcp_server.tools.task_start import task_start
from src.mcp_server.tools.task_update import task_update
from src.mcp_server.tools.task_complete import task_complete

# Decision Tools
from src.mcp_server.tools.decision_add import decision_add

# Documentation Tools (CFA infrastructure)
from src.mcp_server.tools.docs_generate import docs_generate
from src.mcp_server.tools.map_auto_update import map_auto_update
from src.mcp_server.tools.test_coverage_map import test_coverage_map

# =============================================================================
# Feature-Based Tools (imported from src/features/)
# =============================================================================

# Memory Feature (5 tools)
from src.features.memory.tools import (
    memory_set,
    memory_get,
    memory_search,
    memory_list,
    memory_delete,
)

# Orchestration Feature (15 tools)
from src.features.orchestration.tools import (
    agent_route,
    agent_spawn,
    agent_status,
    objective_define,
    objective_check,
    objective_achieve_checkpoint,
    objective_record_iteration,
    objective_fail,
    loop_configure,
    loop_iterate,
    loop_stop,
    loop_status,
    safe_point_create,
    safe_point_rollback,
    safe_point_list,
)

# Knowledge Graph Feature (12 tools)
from src.features.knowledge_graph.tools import (
    kg_build,
    kg_status,
    kg_retrieve,
    kg_expand,
    kg_get,
    kg_search,
    kg_omitted,
    kg_related,
    kg_history,
    kg_blame,
    kg_diff,
    kg_watch,
)

# Symbol Feature (8 tools)
from src.features.symbol.tools import (
    symbol_find,
    symbol_overview,
    symbol_references,
    symbol_replace,
    symbol_insert,
    symbol_rename,
    lsp_status,
    lsp_restart,
)

# File Feature (7 tools)
from src.features.file.tools import (
    file_read,
    file_create,
    file_list,
    file_find,
    file_replace,
    file_edit_lines,
    file_search,
)

# Contract Feature (4 tools)
from src.features.contract.tools import (
    contract_create,
    contract_validate,
    contract_diff,
    contract_sync,
)

# Workflow Feature (4 tools)
from src.features.workflow.tools import (
    workflow_onboard,
    workflow_reflect,
    workflow_summarize,
    workflow_instructions,
)

# Analysis Feature (4 tools)
from src.features.analysis.tools import (
    coupling_analyze,
    dependency_analyze,
    impact_analyze,
    pattern_detect,
)

# Timeline Feature (4 tools)
from src.features.timeline.tools import (
    timeline_checkpoint,
    timeline_rollback,
    timeline_compare,
    timeline_list,
)

# Rules Feature (4 tools)
from src.features.rules.tools import (
    rule_interpret,
    rule_confirm,
    rule_list,
    rule_batch,
)

# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # CFA Core (12)
    "project_init", "project_scan", "project_migrate",
    "context_load", "context_optimize",
    "task_start", "task_update", "task_complete",
    "decision_add",
    "docs_generate", "map_auto_update", "test_coverage_map",
    # Memory (5)
    "memory_set", "memory_get", "memory_search", "memory_list", "memory_delete",
    # Orchestration (15)
    "agent_route", "agent_spawn", "agent_status",
    "objective_define", "objective_check", "objective_achieve_checkpoint",
    "objective_record_iteration", "objective_fail",
    "loop_configure", "loop_iterate", "loop_stop", "loop_status",
    "safe_point_create", "safe_point_rollback", "safe_point_list",
    # Knowledge Graph (12)
    "kg_build", "kg_status", "kg_retrieve", "kg_expand", "kg_get", "kg_search",
    "kg_omitted", "kg_related", "kg_history", "kg_blame", "kg_diff", "kg_watch",
    # Symbol (8)
    "symbol_find", "symbol_overview", "symbol_references",
    "symbol_replace", "symbol_insert", "symbol_rename",
    "lsp_status", "lsp_restart",
    # File (7)
    "file_read", "file_create", "file_list", "file_find",
    "file_replace", "file_edit_lines", "file_search",
    # Contract (4)
    "contract_create", "contract_validate", "contract_diff", "contract_sync",
    # Workflow (4)
    "workflow_onboard", "workflow_reflect", "workflow_summarize", "workflow_instructions",
    # Analysis (4)
    "coupling_analyze", "dependency_analyze", "impact_analyze", "pattern_detect",
    # Timeline (4)
    "timeline_checkpoint", "timeline_rollback", "timeline_compare", "timeline_list",
    # Rules (4)
    "rule_interpret", "rule_confirm", "rule_list", "rule_batch",
]
