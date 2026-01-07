"""
cfa.onboard - Load project context in a single call.

Reads:
- .claude/map.md - Project structure and purpose
- .claude/decisions.md - Architectural decisions (ADRs)
- .claude/current-task.md - Current task state
- .claude/settings.json - Project configuration
- .claude/memories.json - Persistent knowledge (summary)

Can optionally initialize the .claude/ structure if missing.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


# Templates for initialization
MAP_TEMPLATE = """# Project Map

## What This Project Does
<!-- Describe the project purpose in 1-2 sentences -->

## Entry Points
<!-- List main entry points: CLI commands, API endpoints, main files -->

## Directory Structure
```
src/
  features/     # Feature modules
  shared/       # Shared utilities
  core/         # Core functionality
```

## Key Concepts
<!-- List 3-5 key concepts a new developer needs to understand -->

## Non-Obvious Things
<!-- Document gotchas, quirks, or things that aren't obvious from the code -->
"""

DECISIONS_TEMPLATE = """# Architecture Decisions

Record important decisions here. Format:

## YYYY-MM-DD: Decision Title

**Context**: What situation led to this decision?
**Decision**: What was decided?
**Reason**: Why this choice over alternatives?
**Consequences**: What are the trade-offs?

---

<!-- Add decisions below -->
"""

CURRENT_TASK_TEMPLATE = """# Current Task

## Goal
<!-- What are you trying to accomplish? -->

## Status
IN_PROGRESS

## What's Done
- [ ] Step 1

## Blockers
None

## Next Steps
<!-- What comes next? -->
"""

SETTINGS_TEMPLATE = {
    "cfa_version": "4.0",
    "project_name": "",
    "source_root": "src",
    "created_at": ""
}


def _ensure_claude_dir(project_path: str) -> Path:
    """Ensure .claude directory exists."""
    claude_dir = Path(project_path) / ".claude"
    claude_dir.mkdir(exist_ok=True)
    return claude_dir


def _read_file_safe(path: Path) -> Optional[str]:
    """Read file content safely, return None if not exists."""
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return None


def _read_json_safe(path: Path) -> Optional[Dict]:
    """Read JSON file safely, return None if not exists or invalid."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


async def cfa_onboard(
    project_path: str,
    init_if_missing: bool = False,
    include_memories_summary: bool = True,
    max_context_chars: int = 50000
) -> Dict[str, Any]:
    """
    Load project context from .claude/ directory.

    Args:
        project_path: Path to project root
        init_if_missing: Create .claude/ structure if it doesn't exist
        include_memories_summary: Include summary of stored memories
        max_context_chars: Maximum characters to return (truncates if exceeded)

    Returns:
        Dict with project context including map, decisions, task, settings
    """
    project = Path(project_path).resolve()
    claude_dir = project / ".claude"

    # Check if CFA is initialized
    is_initialized = claude_dir.exists() and (claude_dir / "settings.json").exists()

    # Initialize if requested and needed
    if not is_initialized and init_if_missing:
        claude_dir.mkdir(exist_ok=True)

        # Create settings
        settings = SETTINGS_TEMPLATE.copy()
        settings["project_name"] = project.name
        settings["created_at"] = datetime.now().isoformat()
        (claude_dir / "settings.json").write_text(
            json.dumps(settings, indent=2), encoding="utf-8"
        )

        # Create templates
        (claude_dir / "map.md").write_text(MAP_TEMPLATE, encoding="utf-8")
        (claude_dir / "decisions.md").write_text(DECISIONS_TEMPLATE, encoding="utf-8")
        (claude_dir / "current-task.md").write_text(CURRENT_TASK_TEMPLATE, encoding="utf-8")
        (claude_dir / "memories.json").write_text("[]", encoding="utf-8")

        is_initialized = True

    if not is_initialized:
        return {
            "success": False,
            "initialized": False,
            "error": "CFA not initialized. Call with init_if_missing=true to set up.",
            "project_path": str(project)
        }

    # Read all context files
    map_content = _read_file_safe(claude_dir / "map.md") or ""
    decisions_content = _read_file_safe(claude_dir / "decisions.md") or ""
    task_content = _read_file_safe(claude_dir / "current-task.md") or ""
    settings = _read_json_safe(claude_dir / "settings.json") or {}

    # Memories summary
    memories_summary = ""
    if include_memories_summary:
        memories = _read_json_safe(claude_dir / "memories.json") or []
        if memories:
            memories_summary = f"\n\n## Stored Memories ({len(memories)} total)\n"
            for mem in memories[:10]:  # Show first 10
                key = mem.get("key", "unknown")
                tags = ", ".join(mem.get("tags", []))
                memories_summary += f"- **{key}**"
                if tags:
                    memories_summary += f" [{tags}]"
                memories_summary += "\n"
            if len(memories) > 10:
                memories_summary += f"- ... and {len(memories) - 10} more\n"

    # Build context
    context_parts = []

    if map_content:
        context_parts.append(f"# Project Map\n\n{map_content}")

    if decisions_content:
        context_parts.append(f"# Decisions\n\n{decisions_content}")

    if task_content:
        context_parts.append(f"# Current Task\n\n{task_content}")

    if memories_summary:
        context_parts.append(memories_summary)

    full_context = "\n\n---\n\n".join(context_parts)

    # Truncate if needed
    truncated = False
    if len(full_context) > max_context_chars:
        full_context = full_context[:max_context_chars] + "\n\n[TRUNCATED - context exceeds limit]"
        truncated = True

    return {
        "success": True,
        "initialized": True,
        "project_path": str(project),
        "project_name": settings.get("project_name", project.name),
        "cfa_version": settings.get("cfa_version", "4.0"),
        "context": full_context,
        "context_size": len(full_context),
        "truncated": truncated,
        "files_loaded": {
            "map": bool(map_content),
            "decisions": bool(decisions_content),
            "task": bool(task_content),
            "memories": include_memories_summary
        }
    }
