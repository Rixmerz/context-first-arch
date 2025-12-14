"""
MCP Tool: project.scan

Scan project and update map.md with current state.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.map_generator import update_map_file, generate_map, render_map


async def project_scan(project_path: str) -> Dict[str, Any]:
    """
    Scan project and update .claude/map.md.

    Analyzes all code in impl/ and shared/ to generate:
    - Entry points
    - File purpose index
    - Data flow
    - Current state

    Run this after making significant changes to keep map.md current.

    Args:
        project_path: Path to CFA project

    Returns:
        Dictionary with:
            - success: Boolean
            - stats: Analysis statistics
            - map_preview: First 500 chars of generated map

    Example:
        result = await project_scan("/projects/my-app")
        # map.md is now updated with current code analysis
    """
    try:
        path = Path(project_path)
        claude_dir = path / ".claude"

        if not claude_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing .claude/)"
            }

        # Generate and update map
        stats = update_map_file(project_path)

        # Read back for preview
        map_content = (claude_dir / "map.md").read_text()

        return {
            "success": True,
            "stats": stats,
            "file_updated": ".claude/map.md",
            "map_preview": map_content[:800] + "..." if len(map_content) > 800 else map_content,
            "message": f"Map updated: {stats['files_analyzed']} files analyzed, {stats['entry_points_found']} entry points found"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to scan project: {str(e)}"
        }
