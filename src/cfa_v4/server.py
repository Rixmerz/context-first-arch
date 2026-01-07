"""
CFA v4 MCP Server - Simplified

4 tools. Architecture over indexing.

Tools:
- cfa.onboard: Load project context in one call
- cfa.remember: Store knowledge persistently
- cfa.recall: Retrieve stored knowledge
- cfa.checkpoint: Git-based safe points

Philosophy:
- Good architecture makes indexing unnecessary
- Simple tools that do one thing well
- JSON storage, zero dependencies beyond MCP
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools.onboard import cfa_onboard
from .tools.memory import cfa_remember, cfa_recall, cfa_forget
from .tools.checkpoint import cfa_checkpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cfa-v4")

# Create server instance
server = Server("cfa-v4")


# =============================================================================
# TOOL DEFINITIONS (4 tools)
# =============================================================================

TOOLS = [
    Tool(
        name="cfa.onboard",
        description="""[START HERE] Load project context in a single call.

Reads from .claude/ directory:
- map.md: Project structure and purpose
- decisions.md: Architectural decisions (ADRs)
- current-task.md: Current task state
- memories.json: Summary of stored knowledge

Use init_if_missing=true to create .claude/ structure if it doesn't exist.

Call this FIRST in every session.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project root"
                },
                "init_if_missing": {
                    "type": "boolean",
                    "description": "Create .claude/ structure if not exists",
                    "default": False
                },
                "include_memories_summary": {
                    "type": "boolean",
                    "description": "Include summary of stored memories",
                    "default": True
                },
                "max_context_chars": {
                    "type": "number",
                    "description": "Max characters to return",
                    "default": 50000
                }
            },
            "required": ["project_path"]
        }
    ),

    Tool(
        name="cfa.remember",
        description="""[PERSIST KNOWLEDGE] Store learnings across sessions.

Use tags to categorize:
- "pattern": Code patterns discovered
- "gotcha": Non-obvious behaviors or bugs
- "architecture": Structural decisions
- "config": Configuration details

Set append=true to add to existing memory instead of replacing.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project root"
                },
                "key": {
                    "type": "string",
                    "description": "Unique identifier for this memory"
                },
                "value": {
                    "type": "string",
                    "description": "Content to store"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Categories: pattern, gotcha, architecture, config"
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to existing value instead of replacing",
                    "default": False
                }
            },
            "required": ["project_path", "key", "value"]
        }
    ),

    Tool(
        name="cfa.recall",
        description="""[RETRIEVE KNOWLEDGE] Search stored memories.

Three ways to search:
1. By exact key: key="auth-flow"
2. By text query: query="authentication" (searches keys and values)
3. By tags: tags=["pattern", "gotcha"]

Combine query and tags for filtered search.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project root"
                },
                "key": {
                    "type": "string",
                    "description": "Exact key to retrieve"
                },
                "query": {
                    "type": "string",
                    "description": "Text to search in keys and values"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags (OR logic)"
                },
                "limit": {
                    "type": "number",
                    "description": "Max results to return",
                    "default": 10
                }
            },
            "required": ["project_path"]
        }
    ),

    Tool(
        name="cfa.checkpoint",
        description="""[SAFE POINTS] Git-based checkpoints for safe rollback.

Actions:
- create: Create checkpoint before risky changes (requires message)
- list: Show available checkpoints
- rollback: Revert to a checkpoint (dry_run=true to preview)

Checkpoints are git commits with [CFA-SAFE] prefix.""",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to project root"
                },
                "action": {
                    "type": "string",
                    "enum": ["create", "list", "rollback"],
                    "description": "Action to perform",
                    "default": "create"
                },
                "message": {
                    "type": "string",
                    "description": "Description for checkpoint (required for create)"
                },
                "checkpoint_id": {
                    "type": "string",
                    "description": "Commit hash for rollback"
                },
                "include_untracked": {
                    "type": "boolean",
                    "description": "Include untracked files",
                    "default": True
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview without making changes",
                    "default": False
                }
            },
            "required": ["project_path"]
        }
    ),
]


# =============================================================================
# TOOL HANDLERS
# =============================================================================

TOOL_MAP = {
    "cfa.onboard": cfa_onboard,
    "cfa.remember": cfa_remember,
    "cfa.recall": cfa_recall,
    "cfa.checkpoint": cfa_checkpoint,
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
                text=json.dumps({
                    "error": f"Unknown tool: {name}",
                    "available": list(TOOL_MAP.keys())
                })
            )]

        handler = TOOL_MAP[name]
        result = await handler(**arguments)

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        import traceback
        error_msg = f"Error in {name}: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return [TextContent(
            type="text",
            text=json.dumps({"success": False, "error": str(e)})
        )]


# =============================================================================
# SERVER ENTRY POINT
# =============================================================================

async def main():
    """Run the CFA v4 MCP server."""
    from mcp.server.stdio import stdio_server

    logger.info("Starting CFA v4 server...")
    logger.info("Tools: cfa.onboard, cfa.remember, cfa.recall, cfa.checkpoint")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run():
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
