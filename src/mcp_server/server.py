"""
Context-First Architecture + Serena MCP Server

Unified server exposing 44 tools for AI-assisted development:
- CFA Core (20 tools): Project, contract, task, context management
- Symbol Tools (8): Semantic code operations via LSP
- File Tools (7): Enhanced file operations
- Workflow Tools (4): Meta-cognition and reflection
- Memory Tools (5): Persistent project knowledge
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

    logger.info(f"Starting CFA + Serena MCP Server with {len(TOOLS)} tools")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
