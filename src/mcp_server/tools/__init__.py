"""MCP Tools for Context-First Architecture v3 - Optimized (27 tools).

Tools organized by category:
- Workflow (1): Session initialization
- Knowledge Graph (6): Context retrieval & search
- Memory (5): Persistent learnings
- Safe Points (3): Git checkpoints
- Project (2): Setup & migration
- Contract (4): Interface documentation
- Analysis (2): Dependencies & patterns
- Rules (3): Business logic capture
- Decision (1): Architecture records

Consolidated tools use mode/operation parameters:
- kg.context: modes expand|get|related
- kg.git: operations history|blame|diff
- analyze.structure: with/without target
- analyze.change: with/without file_path
"""

# =============================================================================
# MCP Server Tools (used directly in server.py)
# =============================================================================

# Project Tools (2)
from src.mcp_server.tools.project_init import project_init
from src.mcp_server.tools.project_migrate import project_migrate
from src.mcp_server.tools.project_scan import project_scan  # Used internally by kg.build wrapper

# Contract Tools (4)
from src.mcp_server.tools.contract_create import contract_create
from src.mcp_server.tools.contract_validate import contract_validate
from src.mcp_server.tools.contract_sync import contract_sync
from src.mcp_server.tools.contract_diff import contract_diff  # Used internally by contract.sync wrapper
from src.mcp_server.tools.contract_check_breaking import contract_check_breaking

# Decision Tools (1)
from src.mcp_server.tools.decision_add import decision_add

# Analysis Tools (4 - consolidated to 2 in MCP)
from src.mcp_server.tools.dependency_analyze import dependency_analyze
from src.mcp_server.tools.coupling_analyze import coupling_analyze
from src.mcp_server.tools.impact_analyze import impact_analyze
from src.mcp_server.tools.pattern_detect import pattern_detect

# Memory Tools (5) - re-exports from features
from src.mcp_server.tools.memory_set import memory_set
from src.mcp_server.tools.memory_get import memory_get
from src.mcp_server.tools.memory_search import memory_search
from src.mcp_server.tools.memory_list import memory_list
from src.mcp_server.tools.memory_delete import memory_delete

# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Project (2 + 1 internal)
    "project_init", "project_migrate", "project_scan",
    # Contract (4 + 1 internal)
    "contract_create", "contract_validate", "contract_sync",
    "contract_diff", "contract_check_breaking",
    # Decision (1)
    "decision_add",
    # Analysis (4 internal, 2 exposed)
    "dependency_analyze", "coupling_analyze", "impact_analyze", "pattern_detect",
    # Memory (5)
    "memory_set", "memory_get", "memory_search", "memory_list", "memory_delete",
]
