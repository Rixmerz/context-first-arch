"""MCP Tools for Context-First Architecture + Serena Integration."""

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

# Memory Tools
from src.mcp_server.tools.memory_set import memory_set
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_edit import memory_edit
from src.mcp_server.tools.memory_delete import memory_delete

# Symbol Tools (Serena Integration)
from src.mcp_server.tools.symbol_find import symbol_find
from src.mcp_server.tools.symbol_overview import symbol_overview
from src.mcp_server.tools.symbol_references import symbol_references
from src.mcp_server.tools.symbol_replace import symbol_replace
from src.mcp_server.tools.symbol_insert_after import symbol_insert_after
from src.mcp_server.tools.symbol_insert_before import symbol_insert_before
from src.mcp_server.tools.symbol_rename import symbol_rename
from src.mcp_server.tools.lsp_manage import lsp_status, lsp_restart

# File Tools (Serena Integration)
from src.mcp_server.tools.file_read import file_read
from src.mcp_server.tools.file_create import file_create
from src.mcp_server.tools.file_list import file_list
from src.mcp_server.tools.file_find import file_find
from src.mcp_server.tools.file_replace import file_replace
from src.mcp_server.tools.file_lines_delete import file_lines_delete
from src.mcp_server.tools.file_lines_replace import file_lines_replace
from src.mcp_server.tools.file_lines_insert import file_lines_insert
from src.mcp_server.tools.file_search import file_search

# Workflow Tools (Serena Integration)
from src.mcp_server.tools.workflow_onboard import workflow_onboard
from src.mcp_server.tools.workflow_check_onboard import workflow_check_onboard
from src.mcp_server.tools.workflow_think_info import workflow_think_info
from src.mcp_server.tools.workflow_think_task import workflow_think_task
from src.mcp_server.tools.workflow_think_done import workflow_think_done
from src.mcp_server.tools.workflow_summarize import workflow_summarize
from src.mcp_server.tools.workflow_instructions import workflow_instructions

__all__ = [
    # Project
    "project_init",
    "project_scan",
    "project_migrate",
    # Context
    "context_load",
    "context_optimize",
    # Task
    "task_start",
    "task_update",
    "task_complete",
    # Decision
    "decision_add",
    # Contract
    "contract_create",
    "contract_validate",
    "contract_diff",
    "contract_sync",
    # Analysis
    "dependency_analyze",
    "pattern_detect",
    "impact_analyze",
    "coupling_analyze",
    # Documentation
    "docs_generate",
    "map_auto_update",
    "test_coverage_map",
    # Memory
    "memory_set",
    "memory_get",
    "memory_search",
    "memory_list",
    "memory_edit",
    "memory_delete",
    # Symbol (Serena)
    "symbol_find",
    "symbol_overview",
    "symbol_references",
    "symbol_replace",
    "symbol_insert_after",
    "symbol_insert_before",
    "symbol_rename",
    "lsp_status",
    "lsp_restart",
    # File (Serena)
    "file_read",
    "file_create",
    "file_list",
    "file_find",
    "file_replace",
    "file_lines_delete",
    "file_lines_replace",
    "file_lines_insert",
    "file_search",
    # Workflow (Serena)
    "workflow_onboard",
    "workflow_check_onboard",
    "workflow_think_info",
    "workflow_think_task",
    "workflow_think_done",
    "workflow_summarize",
    "workflow_instructions",
]
