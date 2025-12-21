"""
SSE Server for Context-First MCP (CFA v3 + Serena + Nova)

Converts the MCP STDIO server to HTTP/SSE endpoints for embedding in Nova.

Architecture:
- FastAPI for HTTP endpoints
- SSE (Server-Sent Events) for streaming responses
- 84 tools total (72 core + 6 Phase 6 config + 6 SSE-specific)
- Managed as subprocess by Nova

Endpoints:
- POST /mcp/execute - Execute a tool and return result
- GET  /mcp/stream  - SSE stream for long-running operations
- GET  /health      - Health check endpoint
- GET  /tools       - List all available tools
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Phase 6: Import for tool filtering
from src.core.orchestration.storage import OrchestrationStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Context-First MCP SSE Server",
    description="AI-assisted development tools via HTTP/SSE",
    version="3.0.0"
)

# CORS middleware for Nova frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "http://localhost:8765",
        "http://127.0.0.1:8765"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import all MCP tools (same as STDIO server)
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

# Memory Tools
from src.features.memory.tools.memory_set import memory_set
from src.features.memory.tools.memory_get import memory_get
from src.features.memory.tools.memory_search import memory_search
from src.features.memory.tools.memory_list import memory_list
from src.features.memory.tools.memory_delete import memory_delete

# Symbol Tools
from src.mcp_server.tools.symbol_find import symbol_find
from src.mcp_server.tools.symbol_overview import symbol_overview
from src.mcp_server.tools.symbol_references import symbol_references
from src.mcp_server.tools.symbol_replace import symbol_replace
from src.mcp_server.tools.symbol_insert import symbol_insert
from src.mcp_server.tools.symbol_rename import symbol_rename
from src.mcp_server.tools.lsp_manage import lsp_status, lsp_restart

# File Tools
from src.mcp_server.tools.file_read import file_read
from src.mcp_server.tools.file_create import file_create
from src.mcp_server.tools.file_list import file_list
from src.mcp_server.tools.file_find import file_find
from src.mcp_server.tools.file_replace import file_replace
from src.mcp_server.tools.file_edit_lines import file_edit_lines
from src.mcp_server.tools.file_search import file_search

# Workflow Tools
from src.mcp_server.tools.workflow_onboard import workflow_onboard
from src.mcp_server.tools.workflow_reflect import workflow_reflect
from src.mcp_server.tools.workflow_summarize import workflow_summarize
from src.mcp_server.tools.workflow_instructions import workflow_instructions

# Knowledge Graph Tools
from src.mcp_server.tools.kg_build import kg_build
from src.mcp_server.tools.kg_status import kg_status
from src.mcp_server.tools.kg_retrieve import kg_retrieve
from src.mcp_server.tools.kg_expand import kg_expand
from src.mcp_server.tools.kg_get import kg_get
from src.mcp_server.tools.kg_search import kg_search
from src.mcp_server.tools.kg_omitted import kg_omitted
from src.mcp_server.tools.kg_related import kg_related
from src.mcp_server.tools.kg_history import kg_history
from src.mcp_server.tools.kg_blame import kg_blame
from src.mcp_server.tools.kg_diff import kg_diff
from src.mcp_server.tools.kg_watch import kg_watch

# Business Rules Tools
from src.mcp_server.tools.rule_interpret import rule_interpret
from src.mcp_server.tools.rule_confirm import rule_confirm
from src.mcp_server.tools.rule_list import rule_list
from src.mcp_server.tools.rule_batch import rule_batch

# Timeline Tools
from src.mcp_server.tools.timeline_checkpoint import timeline_checkpoint
from src.mcp_server.tools.timeline_rollback import timeline_rollback
from src.mcp_server.tools.timeline_compare import timeline_compare

# Agent Orchestration Tools
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

# Configuration Tools (Phase 6)
from src.features.orchestration.tools.config_list_prompts import config_list_prompts
from src.features.orchestration.tools.config_update_prompt import config_update_prompt
from src.features.orchestration.tools.config_activate_prompt import config_activate_prompt
from src.features.orchestration.tools.config_list_mcp_configs import config_list_mcp_configs
from src.features.orchestration.tools.config_update_mcp_config import config_update_mcp_config
from src.features.orchestration.tools.config_get_active import config_get_active

# Tool registry (map tool names to functions)
TOOL_REGISTRY: Dict[str, Any] = {
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
    # Decision
    "decision.add": decision_add,
    # Context
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
    # Memory
    "memory.set": memory_set,
    "memory.get": memory_get,
    "memory.search": memory_search,
    "memory.list": memory_list,
    "memory.delete": memory_delete,
    # Symbol
    "symbol.find": symbol_find,
    "symbol.overview": symbol_overview,
    "symbol.references": symbol_references,
    "symbol.replace": symbol_replace,
    "symbol.insert": symbol_insert,
    "symbol.rename": symbol_rename,
    "lsp.status": lsp_status,
    "lsp.restart": lsp_restart,
    # File
    "file.read": file_read,
    "file.create": file_create,
    "file.list": file_list,
    "file.find": file_find,
    "file.replace": file_replace,
    "file.edit_lines": file_edit_lines,
    "file.search": file_search,
    # Workflow
    "workflow.onboard": workflow_onboard,
    "workflow.reflect": workflow_reflect,
    "workflow.summarize": workflow_summarize,
    "workflow.instructions": workflow_instructions,
    # Knowledge Graph
    "kg.build": kg_build,
    "kg.status": kg_status,
    "kg.retrieve": kg_retrieve,
    "kg.expand": kg_expand,
    "kg.get": kg_get,
    "kg.search": kg_search,
    "kg.omitted": kg_omitted,
    "kg.related": kg_related,
    "kg.history": kg_history,
    "kg.blame": kg_blame,
    "kg.diff": kg_diff,
    "kg.watch": kg_watch,
    # Business Rules
    "rule.interpret": rule_interpret,
    "rule.confirm": rule_confirm,
    "rule.list": rule_list,
    "rule.batch": rule_batch,
    # Timeline
    "timeline.checkpoint": timeline_checkpoint,
    "timeline.rollback": timeline_rollback,
    "timeline.compare": timeline_compare,
    # Agent Orchestration
    "agent.route": agent_route,
    "agent.spawn": agent_spawn,
    "agent.status": agent_status,
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
    # Configuration (Phase 6)
    "config.list_prompts": config_list_prompts,
    "config.update_prompt": config_update_prompt,
    "config.activate_prompt": config_activate_prompt,
    "config.list_mcp_configs": config_list_mcp_configs,
    "config.update_mcp_config": config_update_mcp_config,
    "config.get_active": config_get_active,
}

# ============================================================================
# Phase 6: Tool Filtering Infrastructure
# ============================================================================

# Initialize storage for tool access control
# Use .claude directory for Nova orchestration database
_storage: Optional[OrchestrationStorage] = None


def _get_storage() -> OrchestrationStorage:
    """Get or initialize OrchestrationStorage."""
    global _storage
    if _storage is None:
        # Default to user's .claude directory for Nova database
        claude_dir = Path.home() / ".claude"
        _storage = OrchestrationStorage(claude_dir)
    return _storage


def _check_tool_access(instance_id: str, tool_name: str) -> tuple[bool, Optional[str]]:
    """
    Check if an instance has access to a tool.

    Returns:
        (allowed: bool, error_message: Optional[str])
    """
    try:
        storage = _get_storage()

        # Get instance from database
        with storage._get_connection() as conn:
            instance_row = conn.execute(
                "SELECT enabled_tools FROM agent_instances WHERE id = ?",
                [instance_id]
            ).fetchone()

        if not instance_row:
            return False, f"Instance '{instance_id}' not found"

        # Parse enabled_tools (stored as JSON array string)
        enabled_tools_json = instance_row[0]

        # If no tools restriction, allow all
        if not enabled_tools_json:
            return True, None

        # Parse JSON and check if tool is allowed
        enabled_tools = json.loads(enabled_tools_json)

        if tool_name in enabled_tools:
            return True, None

        return False, f"Tool '{tool_name}' not allowed for this instance. Enabled tools: {enabled_tools}"

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse enabled_tools JSON for instance {instance_id}: {e}")
        return False, f"Configuration error: Invalid enabled_tools format"

    except Exception as e:
        logger.error(f"Error checking tool access for instance {instance_id}: {e}")
        return False, f"Internal error during access check: {str(e)}"


# Request/Response models
class ToolExecuteRequest(BaseModel):
    tool: str
    params: Dict[str, Any] = {}
    instance_id: Optional[str] = None  # Phase 6: Instance ID for tool filtering


class ToolExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Nova to verify server is running"""
    return {
        "status": "healthy",
        "server": "context-first-sse",
        "version": "3.0.0",
        "tools": len(TOOL_REGISTRY)
    }


# List all available tools
@app.get("/tools")
async def list_tools():
    """Return list of all available MCP tools"""
    return {
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY)
    }


# Execute tool endpoint
@app.post("/mcp/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest):
    """
    Execute an MCP tool and return the result

    Example:
        POST /mcp/execute
        {
            "tool": "kg.retrieve",
            "params": {
                "project_path": "/path/to/project",
                "task": "Understand authentication flow"
            }
        }
    """
    try:
        tool_name = request.tool
        params = request.params
        instance_id = request.instance_id

        logger.info(f"Executing tool: {tool_name} (instance_id: {instance_id})")

        # Check if tool exists
        if tool_name not in TOOL_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found. Available: {list(TOOL_REGISTRY.keys())}"
            )

        # Phase 6: Check tool access if instance_id is provided
        if instance_id:
            allowed, error_msg = _check_tool_access(instance_id, tool_name)
            if not allowed:
                logger.warning(f"Tool access denied for instance {instance_id}: {error_msg}")
                raise HTTPException(
                    status_code=403,
                    detail=error_msg
                )

        # Get tool function
        tool_func = TOOL_REGISTRY[tool_name]

        # Execute tool (handle both sync and async)
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**params)
        else:
            result = tool_func(**params)

        logger.info(f"Tool '{tool_name}' executed successfully")

        return ToolExecuteResponse(
            success=True,
            result=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing tool '{request.tool}': {str(e)}")
        return ToolExecuteResponse(
            success=False,
            error=str(e)
        )


# SSE stream endpoint for long-running operations
@app.get("/mcp/stream")
async def stream_events(request: Request):
    """
    SSE stream for real-time progress updates

    Usage:
        const eventSource = new EventSource('http://localhost:8765/mcp/stream');
        eventSource.onmessage = (event) => {
            console.log('Progress:', event.data);
        };
    """
    async def event_generator():
        try:
            # Example streaming implementation
            # In future, tools can yield progress updates
            for i in range(5):
                if await request.is_disconnected():
                    break

                yield f"data: {json.dumps({'status': 'processing', 'progress': i * 20})}\n\n"
                await asyncio.sleep(1)

            yield f"data: {json.dumps({'status': 'complete', 'progress': 100})}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream: {str(e)}")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Context-First MCP SSE Server Starting")
    logger.info("=" * 60)
    logger.info(f"Tools available: {len(TOOL_REGISTRY)}")
    logger.info("Server ready for Nova integration")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Context-First MCP SSE Server Shutting Down")


if __name__ == "__main__":
    import uvicorn

    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="info",
        access_log=True
    )
