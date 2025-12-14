"""MCP Tools for Context-First Architecture + Serena Integration.

Consolidated to 44 tools (down from 51) for improved AI agent usability.
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

# Memory Tools (5 tools - consolidated from 6)
from src.mcp_server.tools.memory_set import memory_set  # Now includes append mode (was memory_edit)
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_delete import memory_delete

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
]
