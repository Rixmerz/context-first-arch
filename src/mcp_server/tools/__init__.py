"""MCP Tools for Context-First Architecture v3 + Serena Integration + Nova.

74 tools total (44 core + 15 Knowledge Graph + 15 Agent Orchestration):
- CFA Core (20): Project, contract, task, context management
- Symbol (8): Semantic code operations via LSP
- File (7): Enhanced file operations
- Workflow (4): Meta-cognition and reflection
- Memory (5): Persistent project knowledge
- Knowledge Graph Core (9): Intelligent context retrieval with omission transparency
- Knowledge Graph History (3): Git-based code archaeology
- Business Rules (3): Human-confirmed tacit knowledge capture
- Timeline (4): Snapshot management and rollback
- Agent Orchestration (15): Nova multi-model AI orchestration (CFA v2 compliant)

See README.md "MCP Design Philosophy" section for design decisions.
"""

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

# Contract Tools
from src.mcp_server.tools.contract_create import contract_create
from src.mcp_server.tools.contract_validate import contract_validate
from src.mcp_server.tools.contract_diff import contract_diff
from src.mcp_server.tools.contract_sync import contract_sync

# Analysis Tools
from src.mcp_server.tools.dependency_analyze import dependency_analyze
from src.mcp_server.tools.pattern_detect import pattern_detect
from src.mcp_server.tools.impact_analyze import impact_analyze
from src.mcp_server.tools.coupling_analyze import coupling_analyze

# Documentation Tools
from src.mcp_server.tools.docs_generate import docs_generate
from src.mcp_server.tools.map_auto_update import map_auto_update
from src.mcp_server.tools.test_coverage_map import test_coverage_map

# Memory Tools (5 tools - from features/memory - CFA v2 feature-based structure)
from src.features.memory.tools import (
    memory_set,      # Includes append mode (was memory_edit)
    memory_get,
    memory_search,
    memory_list,
    memory_delete,
)

# Symbol Tools (8 tools - consolidated from 9)
from src.mcp_server.tools.symbol_find import symbol_find
from src.mcp_server.tools.symbol_overview import symbol_overview
from src.mcp_server.tools.symbol_references import symbol_references
from src.mcp_server.tools.symbol_replace import symbol_replace
from src.mcp_server.tools.symbol_insert import symbol_insert  # Consolidates insert_before + insert_after
from src.mcp_server.tools.symbol_rename import symbol_rename
from src.mcp_server.tools.lsp_manage import lsp_status, lsp_restart

# File Tools (7 tools - consolidated from 9)
from src.mcp_server.tools.file_read import file_read
from src.mcp_server.tools.file_create import file_create
from src.mcp_server.tools.file_list import file_list
from src.mcp_server.tools.file_find import file_find
from src.mcp_server.tools.file_replace import file_replace
from src.mcp_server.tools.file_edit_lines import file_edit_lines  # Consolidates delete/replace/insert lines
from src.mcp_server.tools.file_search import file_search

# Workflow Tools (4 tools - consolidated from 7)
from src.mcp_server.tools.workflow_onboard import workflow_onboard  # Now includes check_only mode
from src.mcp_server.tools.workflow_reflect import workflow_reflect  # Consolidates 3 think tools
from src.mcp_server.tools.workflow_summarize import workflow_summarize
from src.mcp_server.tools.workflow_instructions import workflow_instructions

# Knowledge Graph Tools (9 tools - CFA v3)
from src.mcp_server.tools.kg_build import kg_build
from src.mcp_server.tools.kg_status import kg_status
from src.mcp_server.tools.kg_retrieve import kg_retrieve
from src.mcp_server.tools.kg_expand import kg_expand
from src.mcp_server.tools.kg_get import kg_get
from src.mcp_server.tools.kg_search import kg_search
from src.mcp_server.tools.kg_omitted import kg_omitted
from src.mcp_server.tools.kg_related import kg_related
from src.mcp_server.tools.kg_watch import kg_watch

# Knowledge Graph History Tools (3 tools - Phase 2)
from src.mcp_server.tools.kg_history import kg_history
from src.mcp_server.tools.kg_blame import kg_blame
from src.mcp_server.tools.kg_diff import kg_diff

# Business Rules Tools (3 tools - Phase 3)
from src.mcp_server.tools.rule_interpret import rule_interpret
from src.mcp_server.tools.rule_confirm import rule_confirm
from src.mcp_server.tools.rule_list import rule_list

# Timeline Tools (3 tools - Phase 4)
from src.mcp_server.tools.timeline_checkpoint import timeline_checkpoint
from src.mcp_server.tools.timeline_rollback import timeline_rollback
from src.mcp_server.tools.timeline_compare import timeline_compare, timeline_list

# Agent Orchestration Tools (15 tools - Nova Integration - CFA v2 compliant)
from src.mcp_server.tools.agent_route import agent_route
from src.mcp_server.tools.agent_spawn import agent_spawn
from src.mcp_server.tools.agent_status import agent_status
from src.mcp_server.tools.objective_define import objective_define
from src.mcp_server.tools.objective_check import objective_check
from src.mcp_server.tools.objective_achieve_checkpoint import objective_achieve_checkpoint
from src.mcp_server.tools.objective_record_iteration import objective_record_iteration
from src.mcp_server.tools.objective_fail import objective_fail
from src.mcp_server.tools.loop_configure import loop_configure
from src.mcp_server.tools.loop_iterate import loop_iterate
from src.mcp_server.tools.loop_stop import loop_stop
from src.mcp_server.tools.loop_status import loop_status
from src.mcp_server.tools.safe_point_create import safe_point_create
from src.mcp_server.tools.safe_point_rollback import safe_point_rollback
from src.mcp_server.tools.safe_point_list import safe_point_list

__all__ = [
    # Project (3)
    "project_init",
    "project_scan",
    "project_migrate",
    # Context (2)
    "context_load",
    "context_optimize",
    # Task (3)
    "task_start",
    "task_update",
    "task_complete",
    # Decision (1)
    "decision_add",
    # Contract (4)
    "contract_create",
    "contract_validate",
    "contract_diff",
    "contract_sync",
    # Analysis (4)
    "dependency_analyze",
    "pattern_detect",
    "impact_analyze",
    "coupling_analyze",
    # Documentation (3)
    "docs_generate",
    "map_auto_update",
    "test_coverage_map",
    # Memory (5)
    "memory_set",
    "memory_get",
    "memory_search",
    "memory_list",
    "memory_delete",
    # Symbol (8)
    "symbol_find",
    "symbol_overview",
    "symbol_references",
    "symbol_replace",
    "symbol_insert",
    "symbol_rename",
    "lsp_status",
    "lsp_restart",
    # File (7)
    "file_read",
    "file_create",
    "file_list",
    "file_find",
    "file_replace",
    "file_edit_lines",
    "file_search",
    # Workflow (4)
    "workflow_onboard",
    "workflow_reflect",
    "workflow_summarize",
    "workflow_instructions",
    # Knowledge Graph Core (8)
    "kg_build",
    "kg_status",
    "kg_retrieve",
    "kg_expand",
    "kg_get",
    "kg_search",
    "kg_omitted",
    "kg_related",
    "kg_watch",
    # Knowledge Graph History (3)
    "kg_history",
    "kg_blame",
    "kg_diff",
    # Business Rules (3)
    "rule_interpret",
    "rule_confirm",
    "rule_list",
    # Timeline (3)
    "timeline_checkpoint",
    "timeline_rollback",
    "timeline_compare",
    "timeline_list",
    # Agent Orchestration - Nova Integration (15 functions - CFA v2 compliant)
    "agent_route",
    "agent_spawn",
    "agent_status",
    "objective_define",
    "objective_check",
    "objective_achieve_checkpoint",
    "objective_record_iteration",
    "objective_fail",
    "loop_configure",
    "loop_iterate",
    "loop_stop",
    "loop_status",
    "safe_point_create",
    "safe_point_rollback",
    "safe_point_list",
]
