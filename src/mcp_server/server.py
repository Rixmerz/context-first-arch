"""
Context-First Architecture MCP Server (CFA v3) - Streamlined

Unified server exposing 41 high-value tools for AI-assisted development:
- Project (3): init, scan, migrate
- Contract (5): create, validate, diff, sync, check_breaking (NEW!)
- Task (3): start, update, complete - CFA-persisted task tracking
- Decision (1): Architecture Decision Records
- Analysis (4): dependency, pattern, impact, coupling - KG-powered
- Memory (5): Persistent project knowledge across sessions
- Workflow (2): onboard, instructions - entry points
- Knowledge Graph (11): Core (8) + History (3) - intelligent context retrieval
- Business Rules (4): Human-confirmed tacit knowledge capture
- Safe Points (3): Git-based checkpoints and rollback

REMOVED (redundant with Claude Code native tools):
- File tools (7) - Claude Code has Read, Write, Edit, Glob, Grep
- Symbol tools (8) - LSP indexing issues, use native tools
- Timeline tools (3) - duplicates safe_point.*
- Orchestration/Nova (9) - over-engineered, Claude Code has internal loop
- Context tools (2) - workflow.onboard does this better
- Documentation tools (3) - low value, KG replaces
- Workflow reflect/summarize (2) - LLM does this naturally
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
from src.mcp_server.tools.contract_check_breaking import contract_check_breaking

# Task Tools
from src.mcp_server.tools.task_start import task_start
from src.mcp_server.tools.task_update import task_update
from src.mcp_server.tools.task_complete import task_complete

# Decision Tools
from src.mcp_server.tools.decision_add import decision_add

# Context Tools - REMOVED (workflow.onboard does this better)
# from src.mcp_server.tools.context_load import context_load
# from src.mcp_server.tools.context_optimize import context_optimize

# Analysis Tools
from src.mcp_server.tools.dependency_analyze import dependency_analyze
from src.mcp_server.tools.pattern_detect import pattern_detect
from src.mcp_server.tools.impact_analyze import impact_analyze
from src.mcp_server.tools.coupling_analyze import coupling_analyze

# Documentation Tools - REMOVED (low value, KG replaces this)
# from src.mcp_server.tools.docs_generate import docs_generate
# from src.mcp_server.tools.map_auto_update import map_auto_update
# from src.mcp_server.tools.test_coverage_map import test_coverage_map

# ============================================================================
# Memory Tools (5) - Consolidated
# ============================================================================
from src.mcp_server.tools.memory_set import memory_set
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_delete import memory_delete

# ============================================================================
# Symbol Tools - REMOVED (8 tools deprecated due to LSP indexing issues)
# Use native Claude Code tools: Grep, Read, Edit instead
# ============================================================================

# ============================================================================
# File Tools - REMOVED (7 tools deprecated - redundant with Claude Code native)
# Claude Code has: Read, Write, Edit, Glob, Grep
# ============================================================================

# ============================================================================
# Workflow Tools - Entry Points (2) - Consolidated
# Note: reflect and summarize REMOVED (LLM does this naturally)
# ============================================================================
from src.mcp_server.tools.workflow_onboard import workflow_onboard
from src.mcp_server.tools.workflow_instructions import workflow_instructions

# ============================================================================
# Knowledge Graph Core Tools (8) - CFA v3
# ============================================================================
from src.mcp_server.tools.kg_build import kg_build
from src.mcp_server.tools.kg_status import kg_status
from src.mcp_server.tools.kg_retrieve import kg_retrieve
from src.mcp_server.tools.kg_expand import kg_expand
from src.mcp_server.tools.kg_get import kg_get
from src.mcp_server.tools.kg_search import kg_search
from src.mcp_server.tools.kg_omitted import kg_omitted
from src.mcp_server.tools.kg_related import kg_related
# kg_watch REMOVED - unnecessary complexity

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
# Timeline Tools - REMOVED (3 tools deprecated - duplicates safe_point.*)
# Use safe_point.create and safe_point.rollback instead
# ============================================================================

# ============================================================================
# Orchestration Tools - Nova Integration
# Note: objective.* and loop.* REMOVED (over-engineered, Claude Code has internal loop)
# Only safe_point.* retained as useful undo mechanism
# ============================================================================
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
        description="[USE WHEN: Starting work on a new project without .claude/ folder] Creates CFA project structure. BEFORE starting any coding task on a new project, check if .claude/ exists - if not, call this to enable intelligent context retrieval.",
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
        description="[USE WHEN: Project structure has changed significantly] Re-scans project and updates map.md. Call after adding new features/modules or major refactoring to keep project map current.",
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
        description="[USE WHEN: User wants CFA on existing codebase] Converts existing project to CFA structure. Use this instead of project.init when the project already has code but no .claude/ folder.",
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
    # CONTRACT TOOLS (5) - Includes breaking change detection
    # ========================================================================
    Tool(
        name="contract.create",
        description="[USE WHEN: Documenting a stable API/interface] Generates contract.md from implementation. Call when a module's public interface is stable and should be documented for consumers.",
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
        description="[USE WHEN: Before releasing or after refactoring] Validates implementation matches contract. MUST call before completing any task that modified code with an existing contract.",
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
        description="[USE WHEN: Contract validation fails] Shows exact differences between contract and implementation. Call after contract.validate returns issues to see what specifically needs fixing.",
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
        description="[USE WHEN: Implementation intentionally changed] Updates contract to match new implementation. Call when you INTENTIONALLY changed a function signature and want the contract to reflect the new reality.",
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
    Tool(
        name="contract.check_breaking",
        description="[MANDATORY AFTER FUNCTION EDITS] CRITICAL: Call this IMMEDIATELY after modifying ANY function signature (parameters added/removed/reordered, types changed). Finds ALL callers via KG and detects incompatibilities. DO NOT mark task complete until breaking_changes=[] is confirmed. Skipping this WILL cause runtime errors.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "symbol": {"type": "string", "description": "Function/method name to check (e.g., 'calculate_total')"},
                "file_path": {"type": "string", "description": "Optional file path to disambiguate if multiple matches"}
            },
            "required": ["project_path", "symbol"]
        }
    ),

    # ========================================================================
    # TASK TOOLS (3)
    # ========================================================================
    Tool(
        name="task.start",
        description="[USE AT SESSION START] Records current task in CFA project for persistence across sessions. Call AFTER workflow.onboard when starting a complex multi-step task. Enables task.update to track progress.",
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
        description="[USE AFTER EACH MILESTONE] Records progress on current CFA task. Call after completing significant steps, encountering blockers, or modifying files. Keeps task state current for session recovery.",
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
        description="[USE WHEN TASK FINISHED] Marks CFA task as completed with summary. Call ONLY after all steps done AND contract.check_breaking passed (if functions were modified). Archives task for future reference.",
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
        description="[USE WHEN MAKING ARCHITECTURAL CHOICES] Documents WHY a decision was made. MUST call when choosing between libraries, patterns, or approaches. Future sessions will see this context. Prevents re-debating settled decisions.",
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
    # context.load and context.optimize REMOVED (workflow.onboard does this better)

    # ========================================================================
    # ANALYSIS TOOLS (4)
    # ========================================================================
    Tool(
        name="dependency.analyze",
        description="[USE BEFORE REFACTORING] Shows what depends on a file/feature and what it depends on. Call BEFORE moving, renaming, or deleting files to understand blast radius. Detects circular dependencies.",
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
        description="[USE BEFORE ADDING NEW CODE] Detects project's coding patterns (naming, imports, function style). Call when unsure about project conventions. Write new code following detected patterns for consistency.",
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
        description="[USE BEFORE RISKY CHANGES] Calculates risk score and blast radius. Call BEFORE modifying core files, deleting code, or major refactors. If risk=high/critical, create safe_point FIRST. Shows which tests to run after change.",
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
        description="[USE FOR ARCHITECTURE REVIEW] Identifies tightly coupled features that should be decoupled. Call when planning major refactoring or evaluating code quality. High coupling = harder to maintain.",
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
    # DOCUMENTATION TOOLS - REMOVED (low value, KG replaces this)
    # docs.generate, map.auto_update, test.coverage_map
    # ========================================================================

    # ========================================================================
    # MEMORY TOOLS (5) - Consolidated
    # ========================================================================
    Tool(
        name="memory.set",
        description="[USE WHEN LEARNING SOMETHING IMPORTANT] Persists knowledge across sessions. MUST call when discovering: project patterns, gotchas, architectural decisions, environment quirks. Future sessions will retrieve this. Tags: architecture, pattern, gotcha, config, decision.",
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
        description="[USE WHEN RECALLING SPECIFIC KNOWLEDGE] Retrieves previously stored memory by exact key. Call when you remember storing something specific but need the details.",
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
        description="[USE AT SESSION START] Searches stored memories by content or tags. Call AFTER workflow.onboard to check if past sessions learned anything relevant to current task. Query with task-related keywords.",
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
        description="[USE FOR MEMORY OVERVIEW] Lists all stored memories with optional tag filter. Call to see what knowledge has been accumulated about this project across all sessions.",
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
        description="[USE TO REMOVE OUTDATED KNOWLEDGE] Deletes a stored memory that is no longer accurate. Call when a memory contains information that has changed or was incorrect.",
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
    # SYMBOL TOOLS - REMOVED (8 tools deprecated due to LSP indexing issues)
    # Use native Claude Code tools: Grep, Read, Edit instead
    # ========================================================================

    # ========================================================================
    # FILE TOOLS - REMOVED (7 tools deprecated - redundant with Claude Code)
    # Claude Code has: Read, Write, Edit, Glob, Grep
    # ========================================================================

    # ========================================================================
    # WORKFLOW TOOLS - Serena (4) - Consolidated
    # ========================================================================
    Tool(
        name="workflow.onboard",
        description="[MANDATORY AT SESSION START] Loads project context including map, decisions, and current task state. Call this FIRST in every session on a CFA project. Tells you what the project is, current state, and what was being worked on. DO NOT start coding without calling this first.",
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
    # workflow.reflect and workflow.summarize REMOVED (LLM does this naturally)
    Tool(
        name="workflow.instructions",
        description="""[START HERE] IMPORTANT: This is the PRIMARY tool for learning Context-First Architecture (CFA).
Please consider as the FIRST CHOICE at the start of any development session.
Call this tool FIRST in any new session to understand what CFA is and how to use its tools.

Context-First Architecture (CFA) v3 is an AI-assisted development framework that provides:
1. Knowledge Graph - Intelligent, task-aware context retrieval from your codebase
2. Omission Transparency - Always know what code you CAN and CANNOT see
3. Contracts - Interface definitions that document boundaries between components
4. Memory - Persistent storage for learnings across sessions
5. Safe Points - Git-based checkpoints for risky operations
6. Task Tracking - Structured workflow for development tasks

The workflow.instructions tool should be used in the following cases:
* At the START of every new development session (MANDATORY)
* When you don't know what CFA tools are available
* When you need to understand the CFA workflow
* Before starting work on any CFA project

Examples of when to call this:
* Starting a new coding session
* "How do I use CFA?"
* "What tools are available?"

After calling this, ALWAYS call workflow.onboard() to load project context.

CRITICAL: At the START of every development session, you MUST:
1. Call workflow.instructions() to learn CFA methodology
2. Call workflow.onboard() to load project context
3. Check if Knowledge Graph exists - if not, suggest kg.build()

DO NOT skip these steps. DO NOT start coding without context.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # KNOWLEDGE GRAPH CORE TOOLS (8) - CFA v3
    # ========================================================================
    Tool(
        name="kg.build",
        description="[REQUIRED BEFORE kg.retrieve] Builds/updates Knowledge Graph from codebase. Call this FIRST when: (1) kg.status shows stale or empty graph, (2) after major code changes, (3) kg.retrieve returns no results. Without an up-to-date graph, context retrieval fails. Use incremental=true after small changes for speed.",
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
        description="[CHECK BEFORE RETRIEVAL] Shows KG health: chunk count, last build time, coverage. Call to diagnose when kg.retrieve returns poor results. If chunks=0 or stale, run kg.build first. Quick diagnostic - use liberally.",
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
        description="[PRIMARY CONTEXT TOOL] THE MOST IMPORTANT CFA TOOL. Call this BEFORE starting any coding task to get task-relevant code context. Describe your task and it returns ranked relevant chunks. Shows BOTH what was loaded AND what was omitted (omission transparency). Use kg.expand to get more context on specific chunks. CRITICAL: Never code blind - always call this first.",
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
        description="[USE AFTER kg.retrieve] Expands context around a specific chunk. Call when kg.retrieve shows a relevant chunk but you need more: its dependencies, what depends on it, or related tests. Pass chunk_id from retrieve results. Prevents incomplete understanding of code relationships.",
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
        description="[USE FOR KNOWN CHUNKS] Retrieves specific chunks by their IDs. Call when you already know exact chunk_ids (from previous kg.retrieve, kg.expand, or kg.related calls) and need to reload their content. More efficient than re-running kg.retrieve for known targets.",
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
        description="[USE FOR KEYWORD SEARCH] BM25-ranked search across codebase. Call when you need to find specific symbols, functions, or text patterns. More precise than kg.retrieve for exact matches. Use for: 'find all usages of X', 'where is Y defined', 'files containing Z'.",
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
        description="[USE WHEN CONTEXT FEELS INCOMPLETE] Analyzes what kg.retrieve chose NOT to include and why. Call when you suspect missing context or kg.retrieve didn't return expected code. Shows omission reasons (token budget, low relevance, filtered type). Helps decide what to kg.expand or include explicitly.",
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
        description="[USE TO TRACE RELATIONSHIPS] Finds all chunks connected to a given chunk: its tests, what it imports, what imports it, related commits, associated business rules. Call when understanding a function's ecosystem: who calls it, what it calls, how it's tested.",
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
        description="[USE TO UNDERSTAND CODE EVOLUTION] Gets git commit history for a chunk or file. Call when you need to understand WHY code is the way it is, what changed recently, or when debugging regressions. Shows commit messages which often explain intent.",
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
        description="[USE TO UNDERSTAND CODE AUTHORSHIP] Links specific lines to the commits that wrote them. Call when you need to understand the reasoning behind specific code decisions - the commit message often explains why.",
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
        description="[USE TO COMPARE VERSIONS] Shows diff between two commits for a file or chunk. Call when debugging what changed between working and broken states, or reviewing recent modifications. Like git diff but chunk-aware.",
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
        description="[USE WHEN ENCOUNTERING COMPLEX LOGIC] Extracts implicit business rules from code for human validation. Call when you see validation logic, authorization checks, or business constraints that aren't documented. Proposes rules that humans must confirm - capturing tacit knowledge before it's lost.",
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
        description="[REQUIRES HUMAN INPUT] Validates proposed business rules with the user. Call to present interpreted rules for human confirmation. CRITICAL: Never assume AI-interpreted rules are correct - always get human confirmation. Supports confirm/correct/reject actions.",
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
        description="[USE TO CHECK EXISTING RULES] Shows confirmed business rules for the project. Call BEFORE modifying code with business logic - check if there are documented rules that must be preserved. Prevents accidentally violating established business constraints.",
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
        description="[USE FOR BULK RULE ACTIONS] Confirms or rejects multiple rules at once. Call when user wants to process many pending rules efficiently. Saves time vs individual rule.confirm calls.",
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
    # TIMELINE TOOLS - REMOVED (3 tools deprecated - duplicates safe_point.*)
    # Use safe_point.create and safe_point.rollback instead
    # ========================================================================

    # ========================================================================
    # ORCHESTRATION TOOLS - Nova Integration (12 MCP tools - CFA v2)
    # Note: Agent tools (route, spawn, status) removed - use Claude Code native Task tool
    # ========================================================================
    # ORCHESTRATION - objective.* and loop.* REMOVED (over-engineered)
    # Only safe_point.* retained as useful undo mechanism
    # ========================================================================
    Tool(
        name="safe_point.create",
        description="[USE BEFORE RISKY CHANGES] Creates git checkpoint for safe rollback. MUST call BEFORE: deleting files, major refactoring, modifying core logic, or any change you're uncertain about. If impact.analyze shows high risk, create safe_point FIRST. Enables undo via safe_point.rollback.",
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
        description="[USE WHEN CHANGES BROKE SOMETHING] Reverts to a previous safe point. Call immediately when: tests fail after changes, unexpected behavior appears, or user says 'undo'. Use mode='preview' first to see what will be reverted, then mode='execute' to apply.",
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
        description="[USE TO SEE UNDO OPTIONS] Lists available safe points to rollback to. Call when user asks 'can we undo?' or before rollback to see available restore points with their summaries and timestamps.",
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
    # Contract (5)
    "contract.create": contract_create,
    "contract.validate": contract_validate,
    "contract.diff": contract_diff,
    "contract.sync": contract_sync,
    "contract.check_breaking": contract_check_breaking,
    # Task
    "task.start": task_start,
    "task.update": task_update,
    "task.complete": task_complete,
    # Decision (context.load/optimize REMOVED - workflow.onboard does this better)
    "decision.add": decision_add,
    # Analysis
    "dependency.analyze": dependency_analyze,
    "pattern.detect": pattern_detect,
    "impact.analyze": impact_analyze,
    "coupling.analyze": coupling_analyze,
    # Documentation - REMOVED (low value, KG replaces this)
    # Memory (5 - consolidated)
    "memory.set": memory_set,
    "memory.get": memory_get,
    "memory.search": memory_search,
    "memory.list": memory_list,
    "memory.delete": memory_delete,
    # Symbol - REMOVED (8 tools deprecated)
    # File - REMOVED (7 tools deprecated - redundant with Claude Code)
    # Workflow (2 - Entry Points only, reflect/summarize REMOVED)
    "workflow.onboard": workflow_onboard,
    "workflow.instructions": workflow_instructions,
    # Knowledge Graph Core (8 - CFA v3)
    "kg.build": kg_build,
    "kg.status": kg_status,
    "kg.retrieve": kg_retrieve,
    "kg.expand": kg_expand,
    "kg.get": kg_get,
    "kg.search": kg_search,
    "kg.omitted": kg_omitted,
    "kg.related": kg_related,
    # kg.watch REMOVED - unnecessary complexity
    # Knowledge Graph History (3 - Phase 2)
    "kg.history": kg_history,
    "kg.blame": kg_blame,
    "kg.diff": kg_diff,
    # Business Rules (4 - Phase 3)
    "rule.interpret": rule_interpret,
    "rule.confirm": rule_confirm,
    "rule.list": rule_list,
    "rule.batch": rule_batch,
    # Timeline - REMOVED (3 tools deprecated - duplicates safe_point.*)
    # Orchestration - objective.* and loop.* REMOVED (over-engineered)
    # Only safe_point.* retained
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
