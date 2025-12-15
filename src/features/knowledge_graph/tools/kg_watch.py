"""
MCP Tool: kg.watch

Control the Knowledge Graph file watcher for automatic updates.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.features.knowledge_graph import (
    start_watcher,
    stop_watcher,
    get_watcher_status,
)


async def kg_watch(
    project_path: str,
    action: str = "status",
    debounce_ms: int = 1000,
    auto_build: bool = True
) -> Dict[str, Any]:
    """
    Control the Knowledge Graph file watcher.

    The watcher monitors file changes and automatically triggers
    incremental Knowledge Graph updates, keeping the graph in sync
    with your codebase as you work.

    Args:
        project_path: Path to CFA project
        action: One of:
            - "start": Start watching for file changes
            - "stop": Stop the watcher
            - "status": Get current watcher status (default)
        debounce_ms: Milliseconds to wait after changes before updating (default: 1000)
        auto_build: If True, automatically rebuild KG on changes (default: True)

    Returns:
        Dictionary with:
            - success: Boolean
            - running: Whether watcher is currently running
            - stats: Watcher statistics (changes detected, builds triggered, etc.)

    Examples:
        # Check watcher status
        result = await kg_watch(project_path="/projects/my-app")

        # Start the watcher
        result = await kg_watch(
            project_path="/projects/my-app",
            action="start",
            debounce_ms=2000  # Wait 2 seconds after changes
        )

        # Stop the watcher
        result = await kg_watch(
            project_path="/projects/my-app",
            action="stop"
        )

    Best Practice:
        Start the watcher when beginning a coding session.
        The watcher automatically updates the KG as you edit files,
        ensuring kg.retrieve always has up-to-date context.

    Note:
        Requires the 'watchdog' package: pip install watchdog
        Or install with: pip install context-first-architecture[watcher]
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/). Run project.init first."
            }

        if action == "start":
            result = start_watcher(
                project_path=path,
                debounce_ms=debounce_ms,
                auto_build=auto_build
            )
            return {
                "success": result.get("success", False),
                "running": result.get("success", False),
                "message": result.get("message") or result.get("error"),
                "stats": result.get("stats", {}),
                "help": (
                    "The watcher is now monitoring file changes. "
                    "Any source file modifications will trigger an incremental KG build."
                ) if result.get("success") else None
            }

        elif action == "stop":
            result = stop_watcher()
            return {
                "success": result.get("success", False),
                "running": False,
                "message": result.get("message") or result.get("error"),
                "final_stats": result.get("final_stats", {})
            }

        elif action == "status":
            result = get_watcher_status()
            return {
                "success": True,
                "running": result.get("running", False),
                "stats": result.get("stats", {}),
                "message": result.get("message", "Watcher status retrieved")
            }

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}. Use 'start', 'stop', or 'status'."
            }

    except ImportError:
        return {
            "success": False,
            "error": (
                "watchdog package not installed. "
                "Install with: pip install watchdog or pip install context-first-architecture[watcher]"
            )
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to control watcher: {str(e)}"
        }
