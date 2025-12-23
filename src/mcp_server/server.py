"""
Context-First Architecture + Serena MCP Server (CFA v3) + Nova Integration

Unified server exposing 65 tools for AI-assisted development:
- CFA Core (20 tools): Project, contract, task, context management
- Symbol Tools (8): Semantic code operations via LSP
- File Tools (7): Enhanced file operations
- Workflow Tools (4): Meta-cognition and reflection
- Memory Tools (5): Persistent project knowledge
- Knowledge Graph Core (8): Intelligent context retrieval with omission transparency
- Knowledge Graph History (3): Git-based code archaeology
- Business Rules (3): Human-confirmed tacit knowledge capture
- Timeline (3): Snapshot management and rollback
- Orchestration (4): Nova loop, objective, safe point management

Note: Agent tools (route, spawn, status) removed - Claude Code native Task tool
with subagent_type now provides equivalent functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent

# ============================================================================
# CFA Core Tools (20)
# ============================================================================

# Project Tools
from src.mcp_server.tools.project_init import project_init
from src.mcp_server.tools.project_scan import project_scan
from src.mcp_server.tools.project_migrate import project_migrate

# Contract Tools
from src.mcp_server.tools.contract_create import contract_create
from src.mcp_server.tools.contract_validate import contract_validate
from src.mcp_server.tools.contract_diff import contract_diff
from src.mcp_server.tools.contract_sync import contract_sync

# Task Tools
from src.mcp_server.tools.task_start import task_start
from src.mcp_server.tools.task_update import task_update
from src.mcp_server.tools.task_complete import task_complete

# Decision Tools
from src.mcp_server.tools.decision_add import decision_add

# Context Tools
from src.mcp_server.tools.context_load import context_load
from src.mcp_server.tools.context_optimize import context_optimize

# Analysis Tools
from src.mcp_server.tools.dependency_analyze import dependency_analyze
from src.mcp_server.tools.pattern_detect import pattern_detect
from src.mcp_server.tools.impact_analyze import impact_analyze
from src.mcp_server.tools.coupling_analyze import coupling_analyze

# Documentation Tools
from src.mcp_server.tools.docs_generate import docs_generate
from src.mcp_server.tools.map_auto_update import map_auto_update
from src.mcp_server.tools.test_coverage_map import test_coverage_map

# ============================================================================
# Memory Tools (5) - Consolidated
# ============================================================================
from src.mcp_server.tools.memory_set import memory_set
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_delete import memory_delete

# ============================================================================
# Symbol Tools - Serena Integration (8) - Consolidated
# ============================================================================
from src.mcp_server.tools.symbol_find import symbol_find
from src.mcp_server.tools.symbol_overview import symbol_overview
from src.mcp_server.tools.symbol_references import symbol_references
from src.mcp_server.tools.symbol_replace import symbol_replace
from src.mcp_server.tools.symbol_insert import symbol_insert
from src.mcp_server.tools.symbol_rename import symbol_rename
from src.mcp_server.tools.lsp_manage import lsp_status, lsp_restart

# ============================================================================
# File Tools - Serena Integration (7) - Consolidated
# ============================================================================
from src.mcp_server.tools.file_read import file_read
from src.mcp_server.tools.file_create import file_create
from src.mcp_server.tools.file_list import file_list
from src.mcp_server.tools.file_find import file_find
from src.mcp_server.tools.file_replace import file_replace
from src.mcp_server.tools.file_edit_lines import file_edit_lines
from src.mcp_server.tools.file_search import file_search

# ============================================================================
# Workflow Tools - Serena Integration (4) - Consolidated
# ============================================================================
from src.mcp_server.tools.workflow_onboard import workflow_onboard
from src.mcp_server.tools.workflow_reflect import workflow_reflect
from src.mcp_server.tools.workflow_summarize import workflow_summarize
from src.mcp_server.tools.workflow_instructions import workflow_instructions

# ============================================================================
# Knowledge Graph Core Tools (9) - CFA v3
# ============================================================================
from src.mcp_server.tools.kg_build import kg_build
from src.mcp_server.tools.kg_status import kg_status
from src.mcp_server.tools.kg_retrieve import kg_retrieve
from src.mcp_server.tools.kg_expand import kg_expand
from src.mcp_server.tools.kg_get import kg_get
from src.mcp_server.tools.kg_search import kg_search
from src.mcp_server.tools.kg_omitted import kg_omitted
from src.mcp_server.tools.kg_related import kg_related
from src.mcp_server.tools.kg_watch import kg_watch

# ============================================================================
# Knowledge Graph History Tools (3) - Phase 2
# ============================================================================
from src.mcp_server.tools.kg_history import kg_history
from src.mcp_server.tools.kg_blame import kg_blame
from src.mcp_server.tools.kg_diff import kg_diff

# ============================================================================
# Business Rules Tools (4) - Phase 3
# ============================================================================
from src.mcp_server.tools.rule_interpret import rule_interpret
from src.mcp_server.tools.rule_confirm import rule_confirm
from src.mcp_server.tools.rule_list import rule_list
from src.mcp_server.tools.rule_batch import rule_batch

# ============================================================================
# Timeline Tools (3) - Phase 4
# ============================================================================
from src.mcp_server.tools.timeline_checkpoint import timeline_checkpoint
from src.mcp_server.tools.timeline_rollback import timeline_rollback
from src.mcp_server.tools.timeline_compare import timeline_compare, timeline_list

# ============================================================================
# Orchestration Tools - Nova Integration (12 MCP tools - CFA v2 compliant)
# Note: Agent tools (route, spawn, status) removed - use Claude Code native Task tool
# ============================================================================
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfa-server")

# Create server instance
server = Server("context-first-architecture")


# ============================================================================
# Tool Definitions (44 total)
# ============================================================================

TOOLS = [
    # ========================================================================
    # PROJECT TOOLS (3)
    # ========================================================================
    Tool(
        name="project.init",
        description="Create new CFA v2 project with optimized structure",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Where to create the project"},
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Brief project description"},
                "languages": {"type": "array", "items": {"type": "string"}, "description": "Languages to support"},
                "cfa_version": {"type": "string", "description": "CFA version (default: 2.0)"},
                "source_root": {"type": "string", "description": "Source root for v2 (default: src)"}
            },
            "required": ["project_path", "name"]
        }
    ),
    Tool(
        name="project.scan",
        description="Scan project and update map.md with analysis",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="project.migrate",
        description="Convert existing project to CFA structure",
        inputSchema={
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Path to existing project"},
                "target_path": {"type": "string", "description": "Where to create CFA project"},
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Project description"},
                "include_tests": {"type": "boolean", "description": "Whether to migrate test files"}
            },
            "required": ["source_path", "target_path"]
        }
    ),

    # ========================================================================
    # CONTRACT TOOLS (4)
    # ========================================================================
    Tool(
        name="contract.create",
        description="Generate contract.md from implementation code",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "impl_file": {"type": "string", "description": "Relative path to implementation"},
                "name": {"type": "string", "description": "Contract name"},
                "purpose": {"type": "string", "description": "Purpose description"}
            },
            "required": ["project_path", "impl_file"]
        }
    ),
    Tool(
        name="contract.validate",
        description="Check implementation matches its contract",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "contract_file": {"type": "string", "description": "Relative path to contract"}
            },
            "required": ["project_path", "contract_file"]
        }
    ),
    Tool(
        name="contract.diff",
        description="Compare contract vs implementation differences",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "contract_file": {"type": "string", "description": "Relative path to contract"},
                "impl_file": {"type": "string", "description": "Optional explicit implementation file"}
            },
            "required": ["project_path", "contract_file"]
        }
    ),
    Tool(
        name="contract.sync",
        description="Update contract from implementation changes",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "impl_file": {"type": "string", "description": "Relative path to implementation"},
                "auto_apply": {"type": "boolean", "description": "Automatically update contract"}
            },
            "required": ["project_path", "impl_file"]
        }
    ),

    # ========================================================================
    # TASK TOOLS (3)
    # ========================================================================
    Tool(
        name="task.start",
        description="[PRIMARY] Begin new task in current-task.md",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "goal": {"type": "string", "description": "What you're trying to accomplish"},
                "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Planned steps"},
                "context": {"type": "string", "description": "Background information"}
            },
            "required": ["project_path", "goal"]
        }
    ),
    Tool(
        name="task.update",
        description="Update progress on current task",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "completed_items": {"type": "array", "items": {"type": "string"}, "description": "Items finished"},
                "files_modified": {"type": "array", "items": {"type": "string"}, "description": "Files changed"},
                "blockers": {"type": "array", "items": {"type": "string"}, "description": "Current blockers"},
                "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Updated next steps"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="task.complete",
        description="Mark current task as completed",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "summary": {"type": "string", "description": "Summary of what was accomplished"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # DECISION & CONTEXT TOOLS (3)
    # ========================================================================
    Tool(
        name="decision.add",
        description="Document architecture decision in decisions.md",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "title": {"type": "string", "description": "Decision title"},
                "context": {"type": "string", "description": "What situation led to this"},
                "decision": {"type": "string", "description": "What was decided"},
                "reason": {"type": "string", "description": "Why this option was chosen"},
                "options_considered": {"type": "array", "items": {"type": "string"}, "description": "Alternatives"},
                "consequences": {"type": "string", "description": "What this means for the project"}
            },
            "required": ["project_path", "title", "context", "decision", "reason"]
        }
    ),
    Tool(
        name="context.load",
        description="Load map.md + current-task.md (use workflow.onboard for full context)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="context.optimize",
        description="Optimize content for LLM token limits",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "max_tokens": {"type": "number", "description": "Maximum token count"},
                "model": {"type": "string", "description": "Model name for token counting"}
            },
            "required": ["project_path", "file_path"]
        }
    ),

    # ========================================================================
    # ANALYSIS TOOLS (4)
    # ========================================================================
    Tool(
        name="dependency.analyze",
        description="Analyze dependencies for features or files",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "target": {"type": "string", "description": "Feature name or file path"},
                "target_type": {"type": "string", "description": "Either 'feature' or 'file'"},
                "transitive": {"type": "boolean", "description": "Include transitive dependencies"}
            },
            "required": ["project_path", "target"]
        }
    ),
    Tool(
        name="pattern.detect",
        description="Detect code patterns and inconsistencies",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "threshold": {"type": "number", "description": "Consistency threshold (0.0-1.0)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="impact.analyze",
        description="Calculate change impact and blast radius",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "change_type": {"type": "string", "description": "Type: 'add', 'modify', or 'delete'"}
            },
            "required": ["project_path", "file_path"]
        }
    ),
    Tool(
        name="coupling.analyze",
        description="Analyze feature coupling and dependencies",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "high_threshold": {"type": "number", "description": "Threshold for high coupling"},
                "low_threshold": {"type": "number", "description": "Threshold for low coupling"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # DOCUMENTATION TOOLS (3)
    # ========================================================================
    Tool(
        name="docs.generate",
        description="Generate documentation from code and contracts",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "feature": {"type": "string", "description": "Feature name"},
                "output_dir": {"type": "string", "description": "Directory to save docs"}
            },
            "required": ["project_path", "feature"]
        }
    ),
    Tool(
        name="map.auto_update",
        description="Auto-update map.md when files change",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "force": {"type": "boolean", "description": "Force update even if no changes"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="test.coverage_map",
        description="Map test coverage to contract requirements",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "contract_file": {"type": "string", "description": "Relative path to contract"}
            },
            "required": ["project_path", "contract_file"]
        }
    ),

    # ========================================================================
    # MEMORY TOOLS (5) - Consolidated
    # ========================================================================
    Tool(
        name="memory.set",
        description="[PRIMARY] Store learning in memory (supports append mode)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Unique identifier for the memory"},
                "value": {"type": "string", "description": "Content to store"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                "append": {"type": "boolean", "description": "Append to existing instead of replace"}
            },
            "required": ["project_path", "key", "value"]
        }
    ),
    Tool(
        name="memory.get",
        description="Retrieve memory by key",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Memory identifier"}
            },
            "required": ["project_path", "key"]
        }
    ),
    Tool(
        name="memory.search",
        description="Search memories by query and/or tags",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "query": {"type": "string", "description": "Text to search"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to filter by"},
                "limit": {"type": "number", "description": "Maximum results"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="memory.list",
        description="List all stored memories",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "limit": {"type": "number", "description": "Maximum memories to return"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="memory.delete",
        description="Delete a stored memory",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Memory identifier to delete"}
            },
            "required": ["project_path", "key"]
        }
    ),

    # ========================================================================
    # SYMBOL TOOLS - Serena (8) - Consolidated
    # ========================================================================
    Tool(
        name="symbol.find",
        description="[PRIMARY] Find symbols (functions, classes) by name",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "symbol_name": {"type": "string", "description": "Name to find (partial match)"},
                "file_path": {"type": "string", "description": "Limit search to specific file"},
                "symbol_kind": {"type": "string", "description": "Filter: function, class, method, variable"},
                "include_body": {"type": "boolean", "description": "Include symbol body"},
                "max_results": {"type": "number", "description": "Maximum results"}
            },
            "required": ["project_path", "symbol_name"]
        }
    ),
    Tool(
        name="symbol.overview",
        description="Get hierarchical symbol structure of a file",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "max_depth": {"type": "number", "description": "Maximum nesting depth"},
                "max_chars": {"type": "number", "description": "Maximum output characters"}
            },
            "required": ["project_path", "file_path"]
        }
    ),
    Tool(
        name="symbol.references",
        description="Find all references to a symbol",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "File containing the symbol"},
                "line": {"type": "number", "description": "Line number (1-indexed)"},
                "column": {"type": "number", "description": "Column number (1-indexed)"},
                "context_lines": {"type": "number", "description": "Context lines around each reference"}
            },
            "required": ["project_path", "file_path", "line", "column"]
        }
    ),
    Tool(
        name="symbol.replace",
        description="[PRIMARY] Replace symbol body. Use for code changes",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "File containing the symbol"},
                "symbol_name": {"type": "string", "description": "Name of symbol to replace"},
                "new_body": {"type": "string", "description": "New implementation code"}
            },
            "required": ["project_path", "file_path", "symbol_name", "new_body"]
        }
    ),
    Tool(
        name="symbol.insert",
        description="Insert content before/after a symbol",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "File containing the symbol"},
                "symbol_name": {"type": "string", "description": "Symbol to insert relative to"},
                "content": {"type": "string", "description": "Code to insert"},
                "position": {"type": "string", "enum": ["before", "after"], "description": "before or after (default: after)"}
            },
            "required": ["project_path", "file_path", "symbol_name", "content"]
        }
    ),
    Tool(
        name="symbol.rename",
        description="Rename symbol across entire project",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "File with symbol definition"},
                "old_name": {"type": "string", "description": "Current symbol name"},
                "new_name": {"type": "string", "description": "New symbol name"}
            },
            "required": ["project_path", "file_path", "old_name", "new_name"]
        }
    ),
    Tool(
        name="lsp.status",
        description="Get LSP server status",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="lsp.restart",
        description="Restart LSP server(s)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "language": {"type": "string", "description": "Specific language to restart (optional)"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # FILE TOOLS - Serena (7) - Consolidated
    # ========================================================================
    Tool(
        name="file.read",
        description="Read file with optional line range",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "start_line": {"type": "number", "description": "Starting line (1-indexed)"},
                "end_line": {"type": "number", "description": "Ending line (1-indexed)"},
                "include_line_numbers": {"type": "boolean", "description": "Prefix lines with numbers"}
            },
            "required": ["project_path", "file_path"]
        }
    ),
    Tool(
        name="file.create",
        description="Create new file with content",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "Relative path for new file"},
                "content": {"type": "string", "description": "Content to write"},
                "overwrite": {"type": "boolean", "description": "Overwrite if exists"},
                "create_directories": {"type": "boolean", "description": "Create parent dirs"}
            },
            "required": ["project_path", "file_path"]
        }
    ),
    Tool(
        name="file.list",
        description="List directory contents with filters",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "directory": {"type": "string", "description": "Directory to list"},
                "recursive": {"type": "boolean", "description": "List recursively"},
                "pattern": {"type": "string", "description": "Glob pattern filter"},
                "include_hidden": {"type": "boolean", "description": "Include hidden files"},
                "max_depth": {"type": "number", "description": "Max recursion depth"},
                "file_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by extensions"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="file.find",
        description="Find files matching pattern (glob/regex)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "pattern": {"type": "string", "description": "Glob or regex pattern"},
                "directory": {"type": "string", "description": "Starting directory"},
                "use_regex": {"type": "boolean", "description": "Use regex instead of glob"},
                "include_hidden": {"type": "boolean", "description": "Include hidden files"},
                "max_results": {"type": "number", "description": "Maximum results"}
            },
            "required": ["project_path", "pattern"]
        }
    ),
    Tool(
        name="file.replace",
        description="Search/replace in file. Use symbol.replace for code",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "search": {"type": "string", "description": "String or pattern to find"},
                "replace": {"type": "string", "description": "Replacement string"},
                "use_regex": {"type": "boolean", "description": "Use regex matching"},
                "count": {"type": "number", "description": "Max replacements (0=all)"},
                "case_sensitive": {"type": "boolean", "description": "Case sensitive"}
            },
            "required": ["project_path", "file_path", "search", "replace"]
        }
    ),
    Tool(
        name="file.edit_lines",
        description="Delete/replace/insert lines. Use symbol.* for code",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "file_path": {"type": "string", "description": "Relative path to file"},
                "operation": {"type": "string", "enum": ["delete", "replace", "insert"], "description": "Operation type"},
                "lines": {"description": "Lines: number, [list], or 'range' for delete/insert"},
                "content": {"type": "string", "description": "Content for replace/insert"},
                "start_line": {"type": "number", "description": "Start line for replace"},
                "end_line": {"type": "number", "description": "End line for replace"},
                "insert_after": {"type": "boolean", "description": "Insert after line (for insert)"}
            },
            "required": ["project_path", "file_path", "operation"]
        }
    ),
    Tool(
        name="file.search",
        description="[PRIMARY] Search for patterns across files (grep)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "pattern": {"type": "string", "description": "Search pattern"},
                "directory": {"type": "string", "description": "Directory to search"},
                "file_pattern": {"type": "string", "description": "Glob for files (e.g. *.py)"},
                "use_regex": {"type": "boolean", "description": "Use regex matching"},
                "case_sensitive": {"type": "boolean", "description": "Case sensitive"},
                "context_lines": {"type": "number", "description": "Context lines around matches"},
                "max_results": {"type": "number", "description": "Maximum matches"},
                "include_hidden": {"type": "boolean", "description": "Include hidden files"}
            },
            "required": ["project_path", "pattern"]
        }
    ),

    # ========================================================================
    # WORKFLOW TOOLS - Serena (4) - Consolidated
    # ========================================================================
    Tool(
        name="workflow.onboard",
        description="[START HERE] Load project context. Use check_only=true to verify freshness",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "check_only": {"type": "boolean", "description": "Only check status, don't load full context"},
                "include_contracts": {"type": "boolean", "description": "Include contract summaries"},
                "include_decisions": {"type": "boolean", "description": "Include decisions"},
                "max_context_size": {"type": "number", "description": "Max context size in chars"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="workflow.reflect",
        description="Structured thinking: type=info|task|done",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "reflect_type": {"type": "string", "enum": ["info", "task", "done"], "description": "Reflection type"},
                "content": {"type": "string", "description": "Content to reflect on"},
                "context": {"type": "string", "description": "Additional context"},
                "questions": {"type": "array", "items": {"type": "string"}, "description": "Questions to consider (for info)"},
                "concerns": {"type": "array", "items": {"type": "string"}, "description": "Concerns to address (for task)"},
                "tests_passed": {"type": "boolean", "description": "Whether tests passed (for done)"}
            },
            "required": ["project_path", "reflect_type", "content"]
        }
    ),
    Tool(
        name="workflow.summarize",
        description="Generate summary of changes made",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "type": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "description": "List of changes made"
                },
                "task_description": {"type": "string", "description": "Task context"}
            },
            "required": ["project_path", "changes"]
        }
    ),
    Tool(
        name="workflow.instructions",
        description="Get CFA workflow guide and best practices",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # KNOWLEDGE GRAPH TOOLS (8) - CFA v3
    # ========================================================================
    Tool(
        name="kg.build",
        description="Build/update Project Knowledge Graph for intelligent retrieval",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "incremental": {"type": "boolean", "description": "Only update changed files"},
                "changed_files": {"type": "array", "items": {"type": "string"}, "description": "Files that changed (for incremental)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.status",
        description="Get Knowledge Graph status and statistics",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.retrieve",
        description="[PRIMARY] Get task-relevant context with full omission transparency",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "task": {"type": "string", "description": "What you're trying to accomplish"},
                "token_budget": {"type": "number", "description": "Maximum tokens (default 30000)"},
                "include_types": {"type": "array", "items": {"type": "string"}, "description": "Chunk types to include"},
                "exclude_types": {"type": "array", "items": {"type": "string"}, "description": "Chunk types to exclude"},
                "include_tests": {"type": "boolean", "description": "Include related tests (default true)"},
                "compression": {"type": "number", "description": "0=full, 1=no_comments, 2=signatures"},
                "symbols": {"type": "array", "items": {"type": "string"}, "description": "Specific symbols to include"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files to include"},
                "auto_build": {"type": "boolean", "description": "Auto-build graph if needed (default true)"}
            },
            "required": ["project_path", "task"]
        }
    ),
    Tool(
        name="kg.expand",
        description="Expand context from a chunk (dependencies, dependents, tests)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "ID of chunk to expand from"},
                "expansion_type": {"type": "string", "enum": ["dependencies", "dependents", "tests", "all"], "description": "What to expand"},
                "token_budget": {"type": "number", "description": "Maximum tokens (default 5000)"}
            },
            "required": ["project_path", "chunk_id"]
        }
    ),
    Tool(
        name="kg.get",
        description="Get specific chunks by ID",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_ids": {"type": "array", "items": {"type": "string"}, "description": "List of chunk IDs to retrieve"}
            },
            "required": ["project_path", "chunk_ids"]
        }
    ),
    Tool(
        name="kg.search",
        description="Search Knowledge Graph using BM25 ranking",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "query": {"type": "string", "description": "Search query"},
                "chunk_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by chunk types"},
                "limit": {"type": "number", "description": "Maximum results (default 20)"}
            },
            "required": ["project_path", "query"]
        }
    ),
    Tool(
        name="kg.omitted",
        description="Analyze omissions from kg.retrieve (what was NOT loaded)",
        inputSchema={
            "type": "object",
            "properties": {
                "omitted_chunks": {"type": "array", "description": "omitted_chunks from kg.retrieve result"},
                "filter_reason": {"type": "string", "description": "Filter by omission reason"},
                "filter_type": {"type": "string", "description": "Filter by chunk type"},
                "sort_by": {"type": "string", "enum": ["relevance", "tokens", "type"], "description": "Sort order"}
            },
            "required": ["omitted_chunks"]
        }
    ),
    Tool(
        name="kg.related",
        description="Find chunks related to a specific chunk",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "ID of chunk to find relations for"},
                "relation_types": {"type": "array", "items": {"type": "string"}, "description": "Filter relations: tests, dependencies, dependents, commits, rules"}
            },
            "required": ["project_path", "chunk_id"]
        }
    ),

    # ========================================================================
    # KNOWLEDGE GRAPH HISTORY TOOLS (3) - Phase 2
    # ========================================================================
    Tool(
        name="kg.history",
        description="Get git commits that modified a chunk or file",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "Chunk ID to get history for"},
                "file_path": {"type": "string", "description": "Direct file path (alternative)"},
                "limit": {"type": "number", "description": "Maximum commits (default 20)"},
                "since": {"type": "string", "description": "Only commits since date (e.g., '1 week ago')"},
                "include_diff": {"type": "boolean", "description": "Include diff content"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.blame",
        description="Find who wrote specific code and why (links lines to commits)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "Chunk ID to blame"},
                "file_path": {"type": "string", "description": "Direct file path"},
                "line_start": {"type": "number", "description": "Start line (1-indexed)"},
                "line_end": {"type": "number", "description": "End line"},
                "group_by_commit": {"type": "boolean", "description": "Group by commit (default true)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.diff",
        description="Compare code between two commits",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "commit_a": {"type": "string", "description": "First commit (older)"},
                "commit_b": {"type": "string", "description": "Second commit (newer, default HEAD)"},
                "file_path": {"type": "string", "description": "Focus on specific file"},
                "chunk_id": {"type": "string", "description": "Focus on chunk's file"},
                "context_lines": {"type": "number", "description": "Context lines (default 3)"}
            },
            "required": ["project_path", "commit_a"]
        }
    ),

    # ========================================================================
    # BUSINESS RULES TOOLS (3) - Phase 3
    # ========================================================================
    Tool(
        name="rule.interpret",
        description="AI interprets business rules from code (proposes for human review)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "Chunk ID to interpret rules from"},
                "file_path": {"type": "string", "description": "Direct file path to analyze"},
                "symbol_name": {"type": "string", "description": "Specific symbol to focus on"},
                "auto_propose": {"type": "boolean", "description": "Auto-save proposed rules (default true)"},
                "categories": {"type": "array", "items": {"type": "string"}, "description": "Filter categories: validation, authorization, business_logic, constraint"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="rule.confirm",
        description="[HUMAN] Confirm, correct, or reject proposed business rules",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "rule_id": {"type": "string", "description": "ID of rule to act on"},
                "action": {"type": "string", "enum": ["confirm", "correct", "reject"], "description": "Action to take"},
                "correction": {"type": "string", "description": "If action=correct, the corrected rule text"},
                "rejection_reason": {"type": "string", "description": "If action=reject, why it was rejected"},
                "confirmed_by": {"type": "string", "description": "Who is confirming (default 'human')"}
            },
            "required": ["project_path", "rule_id", "action"]
        }
    ),
    Tool(
        name="rule.list",
        description="List business rules with filtering",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "status": {"type": "string", "description": "Filter: proposed, confirmed, corrected, rejected"},
                "category": {"type": "string", "description": "Filter: validation, authorization, business_logic, etc."},
                "file_path": {"type": "string", "description": "Filter by source file"},
                "chunk_id": {"type": "string", "description": "Get rules for specific chunk"},
                "pending_only": {"type": "boolean", "description": "Only show rules awaiting confirmation"},
                "limit": {"type": "number", "description": "Maximum rules (default 50)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="rule.batch",
        description="Batch confirm or reject multiple business rules at once",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "rule_ids": {"type": "array", "items": {"type": "string"}, "description": "List of rule IDs to process"},
                "action": {"type": "string", "enum": ["confirm", "reject"], "description": "Action: confirm or reject"},
                "reason": {"type": "string", "description": "Reason (required for reject)"}
            },
            "required": ["project_path", "rule_ids", "action"]
        }
    ),

    # ========================================================================
    # TIMELINE TOOLS (3) - Phase 4
    # ========================================================================
    Tool(
        name="timeline.checkpoint",
        description="[SAFETY] Create snapshot before risky operations",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "name": {"type": "string", "description": "Short name (e.g., 'before-refactor')"},
                "description": {"type": "string", "description": "What this checkpoint captures"},
                "snapshot_type": {"type": "string", "enum": ["user", "agent"], "description": "'user' (manual) or 'agent' (automatic)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
            },
            "required": ["project_path", "name"]
        }
    ),
    Tool(
        name="timeline.rollback",
        description="[CAUTION] Return to previous snapshot state",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "snapshot_id": {"type": "string", "description": "ID of snapshot to rollback to"},
                "mode": {"type": "string", "enum": ["preview", "execute"], "description": "'preview' or 'execute'"},
                "include_git": {"type": "boolean", "description": "Also reset git (dangerous!)"}
            },
            "required": ["project_path", "snapshot_id"]
        }
    ),
    Tool(
        name="timeline.compare",
        description="Compare two snapshots to see what changed",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "snapshot_a": {"type": "string", "description": "First snapshot ID (older)"},
                "snapshot_b": {"type": "string", "description": "Second snapshot ID (newer, or current)"},
                "include_details": {"type": "boolean", "description": "Include file-level details"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # ORCHESTRATION TOOLS - Nova Integration (12 MCP tools - CFA v2)
    # Note: Agent tools (route, spawn, status) removed - use Claude Code native Task tool
    # ========================================================================
    Tool(
        name="objective.define",
        description="[NOVA] Define end-to-end objective with success criteria and checkpoints",
        inputSchema={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "What needs to be accomplished"},
                "success_criteria": {"type": "array", "items": {"type": "string"}, "description": "Specific criteria for success"},
                "checkpoints": {"type": "array", "items": {"type": "string"}, "description": "Milestone descriptions"},
                "max_iterations": {"type": "number", "description": "Max iterations before failure (default 10)"},
                "project_path": {"type": "string", "description": "Optional CFA project path"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for organization"},
                "auto_activate": {"type": "boolean", "description": "Make this the active objective (default true)"}
            },
            "required": ["description"]
        }
    ),
    Tool(
        name="objective.check",
        description="[NOVA] Check progress on objectives and checkpoints",
        inputSchema={
            "type": "object",
            "properties": {
                "objective_id": {"type": "string", "description": "Specific objective (uses active if not provided)"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": []
        }
    ),
    Tool(
        name="objective.achieve_checkpoint",
        description="[NOVA] Mark a checkpoint as achieved within an objective",
        inputSchema={
            "type": "object",
            "properties": {
                "checkpoint_id": {"type": "string", "description": "ID of checkpoint to mark as achieved"},
                "objective_id": {"type": "string", "description": "Optional objective ID (uses active if not provided)"},
                "notes": {"type": "string", "description": "Notes about checkpoint achievement"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": ["checkpoint_id"]
        }
    ),
    Tool(
        name="objective.record_iteration",
        description="[NOVA] Record an iteration attempt for an objective",
        inputSchema={
            "type": "object",
            "properties": {
                "objective_id": {"type": "string", "description": "Optional objective ID (uses active if not provided)"},
                "summary": {"type": "string", "description": "Summary of what was attempted this iteration"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": []
        }
    ),
    Tool(
        name="objective.fail",
        description="[NOVA] Mark an objective as failed",
        inputSchema={
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for failure"},
                "objective_id": {"type": "string", "description": "Optional objective ID (uses active if not provided)"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": ["reason"]
        }
    ),
    Tool(
        name="loop.configure",
        description="[NOVA] Configure a new iterative execution loop",
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task to work on iteratively"},
                "condition_type": {"type": "string", "enum": ["objective_complete", "all_checkpoints", "manual"], "description": "When to stop"},
                "max_iterations": {"type": "number", "description": "Max iterations (default 10)"},
                "iteration_delay_ms": {"type": "number", "description": "Delay between iterations (default 1000)"},
                "enable_safe_points": {"type": "boolean", "description": "Create commits after each iteration (default true)"},
                "escalation_threshold": {"type": "number", "description": "Iterations before model escalation (default 5)"},
                "project_path": {"type": "string", "description": "Optional CFA project path"},
                "objective_id": {"type": "string", "description": "Objective to track (uses active if not provided)"}
            },
            "required": ["task"]
        }
    ),
    Tool(
        name="loop.iterate",
        description="[NOVA] Advance to the next iteration of a loop",
        inputSchema={
            "type": "object",
            "properties": {
                "loop_id": {"type": "string", "description": "ID of the loop to iterate"},
                "iteration_result": {"type": "string", "description": "Summary of previous iteration"},
                "files_changed": {"type": "array", "items": {"type": "string"}, "description": "Files changed in iteration"},
                "tokens_used": {"type": "number", "description": "Tokens used in previous iteration"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": ["loop_id"]
        }
    ),
    Tool(
        name="loop.stop",
        description="[NOVA] Stop a running loop",
        inputSchema={
            "type": "object",
            "properties": {
                "loop_id": {"type": "string", "description": "ID of the loop to stop"},
                "reason": {"type": "string", "description": "Reason for stopping"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": ["loop_id"]
        }
    ),
    Tool(
        name="loop.status",
        description="[NOVA] Get status of loops",
        inputSchema={
            "type": "object",
            "properties": {
                "loop_id": {"type": "string", "description": "Optional specific loop ID to query"},
                "project_path": {"type": "string", "description": "Optional CFA project path"}
            },
            "required": []
        }
    ),
    Tool(
        name="safe_point.create",
        description="[NOVA] Create a git safe point as restore point",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root (must be git repo)"},
                "task_summary": {"type": "string", "description": "What was accomplished"},
                "files_changed": {"type": "array", "items": {"type": "string"}, "description": "Specific files to commit"},
                "include_untracked": {"type": "boolean", "description": "Include untracked files (default true)"},
                "dry_run": {"type": "boolean", "description": "Preview without committing"},
                "prefix": {"type": "string", "description": "Commit message prefix (default '[Nova]')"}
            },
            "required": ["project_path", "task_summary"]
        }
    ),
    Tool(
        name="safe_point.rollback",
        description="[NOVA] Rollback to a previous safe point",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "safe_point_id": {"type": "string", "description": "ID of safe point to rollback to (optional, uses latest)"},
                "mode": {"type": "string", "enum": ["preview", "execute"], "description": "preview or execute (default preview)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="safe_point.list",
        description="[NOVA] List available safe points",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Optional project path (uses cwd if not provided)"},
                "limit": {"type": "number", "description": "Maximum number of safe points to return (default 10)"}
            },
            "required": []
        }
    ),
]


# ============================================================================
# Tool Handler Mapping
# ============================================================================

TOOL_MAP = {
    # Project
    "project.init": project_init,
    "project.scan": project_scan,
    "project.migrate": project_migrate,
    # Contract
    "contract.create": contract_create,
    "contract.validate": contract_validate,
    "contract.diff": contract_diff,
    "contract.sync": contract_sync,
    # Task
    "task.start": task_start,
    "task.update": task_update,
    "task.complete": task_complete,
    # Decision & Context
    "decision.add": decision_add,
    "context.load": context_load,
    "context.optimize": context_optimize,
    # Analysis
    "dependency.analyze": dependency_analyze,
    "pattern.detect": pattern_detect,
    "impact.analyze": impact_analyze,
    "coupling.analyze": coupling_analyze,
    # Documentation
    "docs.generate": docs_generate,
    "map.auto_update": map_auto_update,
    "test.coverage_map": test_coverage_map,
    # Memory (5 - consolidated)
    "memory.set": memory_set,
    "memory.get": memory_get,
    "memory.search": memory_search,
    "memory.list": memory_list,
    "memory.delete": memory_delete,
    # Symbol (8 - consolidated)
    "symbol.find": symbol_find,
    "symbol.overview": symbol_overview,
    "symbol.references": symbol_references,
    "symbol.replace": symbol_replace,
    "symbol.insert": symbol_insert,
    "symbol.rename": symbol_rename,
    "lsp.status": lsp_status,
    "lsp.restart": lsp_restart,
    # File (7 - consolidated)
    "file.read": file_read,
    "file.create": file_create,
    "file.list": file_list,
    "file.find": file_find,
    "file.replace": file_replace,
    "file.edit_lines": file_edit_lines,
    "file.search": file_search,
    # Workflow (4 - consolidated)
    "workflow.onboard": workflow_onboard,
    "workflow.reflect": workflow_reflect,
    "workflow.summarize": workflow_summarize,
    "workflow.instructions": workflow_instructions,
    # Knowledge Graph Core (9 - CFA v3)
    "kg.build": kg_build,
    "kg.status": kg_status,
    "kg.retrieve": kg_retrieve,
    "kg.expand": kg_expand,
    "kg.get": kg_get,
    "kg.search": kg_search,
    "kg.omitted": kg_omitted,
    "kg.related": kg_related,
    "kg.watch": kg_watch,
    # Knowledge Graph History (3 - Phase 2)
    "kg.history": kg_history,
    "kg.blame": kg_blame,
    "kg.diff": kg_diff,
    # Business Rules (4 - Phase 3)
    "rule.interpret": rule_interpret,
    "rule.confirm": rule_confirm,
    "rule.list": rule_list,
    "rule.batch": rule_batch,
    # Timeline (3 - Phase 4)
    "timeline.checkpoint": timeline_checkpoint,
    "timeline.rollback": timeline_rollback,
    "timeline.compare": timeline_compare,
    # Orchestration - Nova Integration (12 - CFA v2 compliant)
    "objective.define": objective_define,
    "objective.check": objective_check,
    "objective.achieve_checkpoint": objective_achieve_checkpoint,
    "objective.record_iteration": objective_record_iteration,
    "objective.fail": objective_fail,
    "loop.configure": loop_configure,
    "loop.iterate": loop_iterate,
    "loop.stop": loop_stop,
    "loop.status": loop_status,
    "safe_point.create": safe_point_create,
    "safe_point.rollback": safe_point_rollback,
    "safe_point.list": safe_point_list,
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Return available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool and return results."""
    import json

    if name not in TOOL_MAP:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]

    try:
        result = await TOOL_MAP[name](**arguments)
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]
    except Exception as e:
        logger.exception(f"Tool {name} failed")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    logger.info(f"Starting CFA v3 MCP Server with {len(TOOLS)} tools (including Knowledge Graph)")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
