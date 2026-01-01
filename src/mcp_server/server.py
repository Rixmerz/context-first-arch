"""
Context-First Architecture MCP Server (CFA v3) - Optimized

Consolidated server with 27 high-value tools (down from 41):

CORE TOOLS:
- Workflow (1): onboard (includes instructions)
- Knowledge Graph (6): build, status, retrieve, search, context, git
- Memory (5): set, get, search, list, delete
- Safe Points (3): create, rollback, list

SPECIALIZED TOOLS:
- Project (2): init, migrate (scan merged into kg.build)
- Contract (4): create, validate, sync, check_breaking
- Analysis (2): structure, change (merged from 4)
- Rules (3): interpret, confirm, list (batch merged into confirm)
- Decision (1): add

REMOVED (41 → 27 = -14 tools):
- task.* (3) → Use Claude Code's TodoWrite
- kg.omitted → Already in kg.retrieve response
- kg.expand/get/related → Merged into kg.context
- kg.history/blame/diff → Merged into kg.git
- workflow.instructions → Merged into workflow.onboard
- project.scan → Merged into kg.build
- contract.diff → Merged into contract.sync
- rule.batch → Merged into rule.confirm
- dependency/coupling.analyze → Merged into analyze.structure
- pattern/impact.analyze → Merged into analyze.change
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent

# ============================================================================
# IMPORTS - Consolidated
# ============================================================================

# Project Tools (2 - scan merged into kg.build)
from src.mcp_server.tools.project_init import project_init
from src.mcp_server.tools.project_migrate import project_migrate

# Contract Tools (3 - diff merged into sync)
from src.mcp_server.tools.contract_create import contract_create
from src.mcp_server.tools.contract_validate import contract_validate
from src.mcp_server.tools.contract_sync import contract_sync
from src.mcp_server.tools.contract_check_breaking import contract_check_breaking

# Decision Tools (1)
from src.mcp_server.tools.decision_add import decision_add

# Analysis Tools - Original imports for wrapper functions
from src.mcp_server.tools.dependency_analyze import dependency_analyze
from src.mcp_server.tools.pattern_detect import pattern_detect
from src.mcp_server.tools.impact_analyze import impact_analyze
from src.mcp_server.tools.coupling_analyze import coupling_analyze

# Memory Tools (5)
from src.mcp_server.tools.memory_set import memory_set
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_delete import memory_delete

# Workflow Tools (1 - instructions merged into onboard)
from src.features.workflow.tools import workflow_onboard, workflow_instructions

# Knowledge Graph Core Tools - Original imports for wrapper functions
from src.features.knowledge_graph.tools import (
    kg_build,
    kg_status,
    kg_retrieve,
    kg_expand,
    kg_get,
    kg_search,
    kg_related,
)

# Knowledge Graph History Tools - Original imports for wrapper functions
from src.features.knowledge_graph.tools import kg_history, kg_blame, kg_diff

# Business Rules Tools (3 - batch merged into confirm)
from src.features.rules.tools import rule_interpret, rule_confirm, rule_list, rule_batch

# Safe Points (3)
from src.features.orchestration.tools import (
    safe_point_create,
    safe_point_rollback,
    safe_point_list,
)

# Project scan for kg.build integration
from src.mcp_server.tools.project_scan import project_scan

# Contract diff for contract.sync integration
from src.mcp_server.tools.contract_diff import contract_diff

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfa-server")

# Create server instance
server = Server("context-first-architecture")


# ============================================================================
# CONSOLIDATED TOOL WRAPPERS
# ============================================================================

async def workflow_onboard_consolidated(
    project_path: str,
    show_instructions: bool = False,
    check_only: bool = False,
    include_contracts: bool = True,
    include_decisions: bool = True,
    max_context_size: int = 50000
) -> Dict[str, Any]:
    """Consolidated workflow.onboard that includes instructions."""
    result = {}

    # If show_instructions requested, include CFA instructions
    if show_instructions:
        instructions = await workflow_instructions(project_path=project_path)
        result["instructions"] = instructions

    # Run normal onboard
    onboard_result = await workflow_onboard(
        project_path=project_path,
        check_only=check_only,
        include_contracts=include_contracts,
        include_decisions=include_decisions,
        max_context_size=max_context_size
    )

    result.update(onboard_result)
    return result


async def kg_build_consolidated(
    project_path: str,
    incremental: bool = False,
    changed_files: List[str] = None,
    update_map: bool = True
) -> Dict[str, Any]:
    """Consolidated kg.build that includes project.scan."""
    # Build Knowledge Graph
    build_result = await kg_build(
        project_path=project_path,
        incremental=incremental,
        changed_files=changed_files
    )

    # Also update project map if requested
    if update_map and build_result.get("success"):
        try:
            scan_result = await project_scan(project_path=project_path)
            build_result["map_updated"] = scan_result.get("success", False)
            build_result["map_stats"] = scan_result.get("stats", {})
        except Exception as e:
            build_result["map_updated"] = False
            build_result["map_error"] = str(e)

    return build_result


async def kg_context(
    project_path: str,
    chunk_id: str = None,
    chunk_ids: List[str] = None,
    mode: str = "expand",
    expansion_type: str = "all",
    relation_types: List[str] = None,
    token_budget: int = 5000
) -> Dict[str, Any]:
    """
    Consolidated context retrieval: expand, get, or related.

    Modes:
    - expand: Expand context around a chunk (dependencies, dependents, tests)
    - get: Get specific chunks by IDs
    - related: Find related chunks (tests, dependencies, dependents, commits, rules)
    """
    if mode == "get":
        if not chunk_ids:
            return {"success": False, "error": "chunk_ids required for mode='get'"}
        return await kg_get(project_path=project_path, chunk_ids=chunk_ids)

    elif mode == "related":
        if not chunk_id:
            return {"success": False, "error": "chunk_id required for mode='related'"}
        return await kg_related(
            project_path=project_path,
            chunk_id=chunk_id,
            relation_types=relation_types
        )

    else:  # mode == "expand" (default)
        if not chunk_id:
            return {"success": False, "error": "chunk_id required for mode='expand'"}
        return await kg_expand(
            project_path=project_path,
            chunk_id=chunk_id,
            expansion_type=expansion_type,
            token_budget=token_budget
        )


async def kg_git(
    project_path: str,
    operation: str = "history",
    chunk_id: str = None,
    file_path: str = None,
    commit_a: str = None,
    commit_b: str = "HEAD",
    line_start: int = None,
    line_end: int = None,
    limit: int = 20,
    since: str = None,
    include_diff: bool = False,
    group_by_commit: bool = True,
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Consolidated git operations: history, blame, or diff.

    Operations:
    - history: Get commit history for chunk/file
    - blame: Get line-by-line authorship
    - diff: Compare two commits
    """
    if operation == "blame":
        return await kg_blame(
            project_path=project_path,
            chunk_id=chunk_id,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            group_by_commit=group_by_commit
        )

    elif operation == "diff":
        if not commit_a:
            return {"success": False, "error": "commit_a required for operation='diff'"}
        return await kg_diff(
            project_path=project_path,
            commit_a=commit_a,
            commit_b=commit_b,
            file_path=file_path,
            chunk_id=chunk_id,
            context_lines=context_lines
        )

    else:  # operation == "history" (default)
        return await kg_history(
            project_path=project_path,
            chunk_id=chunk_id,
            file_path=file_path,
            limit=limit,
            since=since,
            include_diff=include_diff
        )


async def analyze_structure(
    project_path: str,
    target: str = None,
    target_type: str = "feature",
    transitive: bool = False,
    high_threshold: float = None,
    low_threshold: float = None
) -> Dict[str, Any]:
    """
    Consolidated structure analysis: dependencies + coupling.

    If target is provided: analyzes dependencies of that target
    If target is None: analyzes overall coupling between features
    """
    if target:
        # Dependency analysis for specific target
        return await dependency_analyze(
            project_path=project_path,
            target=target,
            target_type=target_type,
            transitive=transitive
        )
    else:
        # Overall coupling analysis - filter None values to use defaults
        kwargs = {"project_path": project_path}
        if high_threshold is not None:
            kwargs["high_threshold"] = high_threshold
        if low_threshold is not None:
            kwargs["low_threshold"] = low_threshold
        return await coupling_analyze(**kwargs)


async def analyze_change(
    project_path: str,
    file_path: str = None,
    change_type: str = "modify",
    threshold: float = None
) -> Dict[str, Any]:
    """
    Consolidated change analysis: patterns + impact.

    If file_path is provided: analyzes impact of changing that file
    If file_path is None: detects patterns in the codebase
    """
    if file_path:
        # Impact analysis for specific file
        return await impact_analyze(
            project_path=project_path,
            file_path=file_path,
            change_type=change_type
        )
    else:
        # Pattern detection - filter None to use default
        kwargs = {"project_path": project_path}
        if threshold is not None:
            kwargs["threshold"] = threshold
        return await pattern_detect(**kwargs)


async def contract_sync_consolidated(
    project_path: str,
    impl_file: str,
    preview: bool = False,
    auto_apply: bool = False
) -> Dict[str, Any]:
    """
    Consolidated contract sync with preview (was contract.diff).

    If preview=True: shows diff without applying (was contract.diff)
    If auto_apply=True: automatically updates contract
    """
    if preview:
        # Show diff only (was contract.diff)
        return await contract_diff(
            project_path=project_path,
            contract_file=None,  # Will be inferred from impl_file
            impl_file=impl_file
        )
    else:
        # Sync contract
        return await contract_sync(
            project_path=project_path,
            impl_file=impl_file,
            auto_apply=auto_apply
        )


async def rule_confirm_consolidated(
    project_path: str,
    rule_id: str = None,
    rule_ids: List[str] = None,
    action: str = "confirm",
    correction: str = None,
    rejection_reason: str = None,
    reason: str = None,
    confirmed_by: str = "human"
) -> Dict[str, Any]:
    """
    Consolidated rule confirmation with batch support.

    If rule_ids (array) provided: batch operation
    If rule_id (single) provided: single operation
    """
    if rule_ids and len(rule_ids) > 1:
        # Batch operation
        return await rule_batch(
            project_path=project_path,
            rule_ids=rule_ids,
            action=action,
            reason=reason or rejection_reason
        )
    else:
        # Single operation
        single_id = rule_id or (rule_ids[0] if rule_ids else None)
        if not single_id:
            return {"success": False, "error": "rule_id or rule_ids required"}

        return await rule_confirm(
            project_path=project_path,
            rule_id=single_id,
            action=action,
            correction=correction,
            rejection_reason=rejection_reason,
            confirmed_by=confirmed_by
        )


# ============================================================================
# TOOL DEFINITIONS (27 total - down from 41)
# ============================================================================

TOOLS = [
    # ========================================================================
    # WORKFLOW (1) - Entry point
    # ========================================================================
    Tool(
        name="workflow.onboard",
        description="""[MANDATORY AT SESSION START] Loads project context including map, decisions, and current task state.

Call this FIRST in every session. Set show_instructions=true on first use to learn CFA.

CFA v3 provides:
1. Knowledge Graph - Task-aware context retrieval
2. Omission Transparency - Know what you CAN and CANNOT see
3. Memory - Persistent learnings across sessions
4. Safe Points - Git checkpoints for undo
5. Contracts - Interface documentation

CRITICAL: DO NOT start coding without calling this first.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "show_instructions": {"type": "boolean", "description": "Include CFA usage instructions (use on first session)"},
                "check_only": {"type": "boolean", "description": "Only check status, don't load full context"},
                "include_contracts": {"type": "boolean", "description": "Include contract summaries"},
                "include_decisions": {"type": "boolean", "description": "Include decisions"},
                "max_context_size": {"type": "number", "description": "Max context size in chars"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # KNOWLEDGE GRAPH (6) - Context retrieval
    # ========================================================================
    Tool(
        name="kg.build",
        description="[REQUIRED BEFORE kg.retrieve] Builds Knowledge Graph and updates project map. Call when: (1) kg.status shows stale, (2) after code changes, (3) kg.retrieve returns poor results. Set update_map=false to skip map update.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "incremental": {"type": "boolean", "description": "Only update changed files"},
                "changed_files": {"type": "array", "items": {"type": "string"}, "description": "Files that changed"},
                "update_map": {"type": "boolean", "description": "Also update project map (default true)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.status",
        description="[CHECK BEFORE RETRIEVAL] Shows KG health: chunk count, last build time, coverage. Quick diagnostic - use liberally.",
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
        description="[PRIMARY TOOL] Get task-relevant code context. Returns what was loaded AND what was omitted. Use kg.context to expand specific chunks.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "task": {"type": "string", "description": "What you're trying to accomplish"},
                "token_budget": {"type": "number", "description": "Maximum tokens (default 30000)"},
                "include_types": {"type": "array", "items": {"type": "string"}, "description": "Chunk types to include"},
                "exclude_types": {"type": "array", "items": {"type": "string"}, "description": "Chunk types to exclude"},
                "include_tests": {"type": "boolean", "description": "Include related tests"},
                "compression": {"type": "number", "description": "0=full, 1=no_comments, 2=signatures"},
                "symbols": {"type": "array", "items": {"type": "string"}, "description": "Specific symbols"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files"},
                "auto_build": {"type": "boolean", "description": "Auto-build if needed"}
            },
            "required": ["project_path", "task"]
        }
    ),
    Tool(
        name="kg.search",
        description="[KEYWORD SEARCH] BM25-ranked search for specific symbols, functions, or patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "query": {"type": "string", "description": "Search query"},
                "chunk_types": {"type": "array", "items": {"type": "string"}, "description": "Filter by types"},
                "limit": {"type": "number", "description": "Maximum results"}
            },
            "required": ["project_path", "query"]
        }
    ),
    Tool(
        name="kg.context",
        description="[EXPAND CONTEXT] Get more context for specific chunks. Modes: expand (dependencies/dependents), get (by IDs), related (relationships).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "mode": {"type": "string", "enum": ["expand", "get", "related"], "description": "Operation mode"},
                "chunk_id": {"type": "string", "description": "Single chunk ID (for expand/related)"},
                "chunk_ids": {"type": "array", "items": {"type": "string"}, "description": "Multiple chunk IDs (for get)"},
                "expansion_type": {"type": "string", "enum": ["dependencies", "dependents", "tests", "all"], "description": "What to expand"},
                "relation_types": {"type": "array", "items": {"type": "string"}, "description": "Filter relations"},
                "token_budget": {"type": "number", "description": "Maximum tokens"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="kg.git",
        description="[GIT OPERATIONS] History, blame, or diff. Operations: history (commits), blame (authorship), diff (compare versions).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "operation": {"type": "string", "enum": ["history", "blame", "diff"], "description": "Git operation"},
                "chunk_id": {"type": "string", "description": "Chunk ID"},
                "file_path": {"type": "string", "description": "File path"},
                "commit_a": {"type": "string", "description": "First commit (for diff)"},
                "commit_b": {"type": "string", "description": "Second commit (for diff)"},
                "line_start": {"type": "number", "description": "Start line (for blame)"},
                "line_end": {"type": "number", "description": "End line (for blame)"},
                "limit": {"type": "number", "description": "Max commits (for history)"},
                "since": {"type": "string", "description": "Since date (for history)"},
                "include_diff": {"type": "boolean", "description": "Include diffs (for history)"},
                "context_lines": {"type": "number", "description": "Context lines (for diff)"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # MEMORY (5) - Persistent knowledge
    # ========================================================================
    Tool(
        name="memory.set",
        description="[PERSIST KNOWLEDGE] Store learnings across sessions. Tags: architecture, pattern, gotcha, config.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Unique identifier"},
                "value": {"type": "string", "description": "Content to store"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                "append": {"type": "boolean", "description": "Append instead of replace"}
            },
            "required": ["project_path", "key", "value"]
        }
    ),
    Tool(
        name="memory.get",
        description="[RECALL] Retrieve memory by exact key.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Memory key"}
            },
            "required": ["project_path", "key"]
        }
    ),
    Tool(
        name="memory.search",
        description="[SEARCH MEMORIES] Find memories by content or tags.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "query": {"type": "string", "description": "Search text"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                "limit": {"type": "number", "description": "Max results"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="memory.list",
        description="[LIST MEMORIES] Show all stored memories.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "limit": {"type": "number", "description": "Max results"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="memory.delete",
        description="[DELETE MEMORY] Remove outdated memory.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "key": {"type": "string", "description": "Memory key to delete"}
            },
            "required": ["project_path", "key"]
        }
    ),

    # ========================================================================
    # SAFE POINTS (3) - Git checkpoints
    # ========================================================================
    Tool(
        name="safe_point.create",
        description="[BEFORE RISKY CHANGES] Create git checkpoint for rollback.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project"},
                "task_summary": {"type": "string", "description": "What was done"},
                "files_changed": {"type": "array", "items": {"type": "string"}, "description": "Files to commit"},
                "include_untracked": {"type": "boolean", "description": "Include untracked"},
                "dry_run": {"type": "boolean", "description": "Preview only"},
                "prefix": {"type": "string", "description": "Commit prefix"}
            },
            "required": ["project_path", "task_summary"]
        }
    ),
    Tool(
        name="safe_point.rollback",
        description="[UNDO CHANGES] Revert to previous safe point. Use mode='preview' first.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project"},
                "safe_point_id": {"type": "string", "description": "Safe point ID"},
                "mode": {"type": "string", "enum": ["preview", "execute"], "description": "Preview or execute"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="safe_point.list",
        description="[LIST CHECKPOINTS] Show available safe points.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project"},
                "limit": {"type": "number", "description": "Max results"}
            },
            "required": []
        }
    ),

    # ========================================================================
    # PROJECT (2) - Setup
    # ========================================================================
    Tool(
        name="project.init",
        description="[NEW PROJECT] Create CFA project structure.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Where to create"},
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Description"},
                "languages": {"type": "array", "items": {"type": "string"}, "description": "Languages"},
                "cfa_version": {"type": "string", "description": "CFA version"},
                "source_root": {"type": "string", "description": "Source root"}
            },
            "required": ["project_path", "name"]
        }
    ),
    Tool(
        name="project.migrate",
        description="[EXISTING PROJECT] Convert to CFA structure.",
        inputSchema={
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Existing project"},
                "target_path": {"type": "string", "description": "CFA project location"},
                "name": {"type": "string", "description": "Project name"},
                "description": {"type": "string", "description": "Description"},
                "include_tests": {"type": "boolean", "description": "Migrate tests"}
            },
            "required": ["source_path", "target_path"]
        }
    ),

    # ========================================================================
    # CONTRACT (4) - Interface documentation
    # ========================================================================
    Tool(
        name="contract.create",
        description="[DOCUMENT API] Generate contract from implementation.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "impl_file": {"type": "string", "description": "Implementation file"},
                "name": {"type": "string", "description": "Contract name"},
                "purpose": {"type": "string", "description": "Purpose"}
            },
            "required": ["project_path", "impl_file"]
        }
    ),
    Tool(
        name="contract.validate",
        description="[CHECK CONTRACT] Validate implementation matches contract.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "contract_file": {"type": "string", "description": "Contract file"}
            },
            "required": ["project_path", "contract_file"]
        }
    ),
    Tool(
        name="contract.sync",
        description="[UPDATE CONTRACT] Sync contract with implementation. Use preview=true to see diff first.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "impl_file": {"type": "string", "description": "Implementation file"},
                "preview": {"type": "boolean", "description": "Show diff only (was contract.diff)"},
                "auto_apply": {"type": "boolean", "description": "Auto-apply changes"}
            },
            "required": ["project_path", "impl_file"]
        }
    ),
    Tool(
        name="contract.check_breaking",
        description="[MANDATORY AFTER FUNCTION EDITS] Check for breaking changes after modifying function signatures. Uses Knowledge Graph to find all callers and detect incompatibilities. DO NOT mark task complete until breaking_changes=[].",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "symbol": {"type": "string", "description": "Function/method name to check"},
                "file_path": {"type": "string", "description": "Optional file path to disambiguate"}
            },
            "required": ["project_path", "symbol"]
        }
    ),

    # ========================================================================
    # ANALYSIS (2) - Code intelligence
    # ========================================================================
    Tool(
        name="analyze.structure",
        description="[DEPENDENCIES] Analyze dependencies (with target) or coupling (without target).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "target": {"type": "string", "description": "Feature/file to analyze (omit for coupling)"},
                "target_type": {"type": "string", "description": "'feature' or 'file'"},
                "transitive": {"type": "boolean", "description": "Include transitive deps"},
                "high_threshold": {"type": "number", "description": "High coupling threshold"},
                "low_threshold": {"type": "number", "description": "Low coupling threshold"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="analyze.change",
        description="[IMPACT] Analyze change impact (with file_path) or detect patterns (without).",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "file_path": {"type": "string", "description": "File to analyze (omit for patterns)"},
                "change_type": {"type": "string", "description": "'add', 'modify', or 'delete'"},
                "threshold": {"type": "number", "description": "Pattern threshold"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # RULES (3) - Business logic
    # ========================================================================
    Tool(
        name="rule.interpret",
        description="[EXTRACT RULES] Find business rules in code for human validation.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "chunk_id": {"type": "string", "description": "Chunk to analyze"},
                "file_path": {"type": "string", "description": "File to analyze"},
                "symbol_name": {"type": "string", "description": "Symbol to focus on"},
                "auto_propose": {"type": "boolean", "description": "Auto-save proposals"},
                "categories": {"type": "array", "items": {"type": "string"}, "description": "Categories"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="rule.confirm",
        description="[VALIDATE RULES] Confirm, correct, or reject rules. Accepts single rule_id or array rule_ids for batch.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "rule_id": {"type": "string", "description": "Single rule ID"},
                "rule_ids": {"type": "array", "items": {"type": "string"}, "description": "Multiple rule IDs (batch)"},
                "action": {"type": "string", "enum": ["confirm", "correct", "reject"], "description": "Action"},
                "correction": {"type": "string", "description": "Correction text"},
                "rejection_reason": {"type": "string", "description": "Rejection reason"},
                "confirmed_by": {"type": "string", "description": "Who confirmed"}
            },
            "required": ["project_path", "action"]
        }
    ),
    Tool(
        name="rule.list",
        description="[LIST RULES] Show business rules. Filter by status, category, file.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "status": {"type": "string", "description": "Filter by status"},
                "category": {"type": "string", "description": "Filter by category"},
                "file_path": {"type": "string", "description": "Filter by file"},
                "pending_only": {"type": "boolean", "description": "Only pending"},
                "limit": {"type": "number", "description": "Max results"}
            },
            "required": ["project_path"]
        }
    ),

    # ========================================================================
    # DECISION (1) - Architecture records
    # ========================================================================
    Tool(
        name="decision.add",
        description="[DOCUMENT DECISION] Record architectural choice with reasoning.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to CFA project"},
                "title": {"type": "string", "description": "Decision title"},
                "context": {"type": "string", "description": "Situation"},
                "decision": {"type": "string", "description": "What was decided"},
                "reason": {"type": "string", "description": "Why"},
                "options_considered": {"type": "array", "items": {"type": "string"}, "description": "Alternatives"},
                "consequences": {"type": "string", "description": "Impact"}
            },
            "required": ["project_path", "title", "context", "decision", "reason"]
        }
    ),
]


# ============================================================================
# Tool Handler Mapping (27 tools)
# ============================================================================

TOOL_MAP = {
    # Workflow (1)
    "workflow.onboard": workflow_onboard_consolidated,

    # Knowledge Graph (6)
    "kg.build": kg_build_consolidated,
    "kg.status": kg_status,
    "kg.retrieve": kg_retrieve,
    "kg.search": kg_search,
    "kg.context": kg_context,
    "kg.git": kg_git,

    # Memory (5)
    "memory.set": memory_set,
    "memory.get": memory_get,
    "memory.search": memory_search,
    "memory.list": memory_list,
    "memory.delete": memory_delete,

    # Safe Points (3)
    "safe_point.create": safe_point_create,
    "safe_point.rollback": safe_point_rollback,
    "safe_point.list": safe_point_list,

    # Project (2)
    "project.init": project_init,
    "project.migrate": project_migrate,

    # Contract (4)
    "contract.create": contract_create,
    "contract.validate": contract_validate,
    "contract.sync": contract_sync_consolidated,
    "contract.check_breaking": contract_check_breaking,

    # Analysis (2)
    "analyze.structure": analyze_structure,
    "analyze.change": analyze_change,

    # Rules (3)
    "rule.interpret": rule_interpret,
    "rule.confirm": rule_confirm_consolidated,
    "rule.list": rule_list,

    # Decision (1)
    "decision.add": decision_add,
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Return available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution."""
    try:
        if name not in TOOL_MAP:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}. Available: {', '.join(TOOL_MAP.keys())}"
            )]

        handler = TOOL_MAP[name]
        result = await handler(**arguments)

        # Convert result to JSON string
        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        import traceback
        error_msg = f"Error in {name}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
