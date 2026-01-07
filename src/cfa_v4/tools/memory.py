"""
cfa.remember & cfa.recall - Simple JSON-based persistent memory.

Storage: .claude/memories.json

Format:
[
  {
    "key": "unique-key",
    "value": "what was learned",
    "tags": ["pattern", "gotcha"],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]

No embeddings, no vector DB. Simple text matching.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_memories_path(project_path: str) -> Path:
    """Get path to memories.json."""
    return Path(project_path).resolve() / ".claude" / "memories.json"


def _load_memories(project_path: str) -> List[Dict]:
    """Load memories from JSON file."""
    path = _get_memories_path(project_path)
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_memories(project_path: str, memories: List[Dict]) -> None:
    """Save memories to JSON file."""
    path = _get_memories_path(project_path)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(memories, indent=2, default=str), encoding="utf-8")


async def cfa_remember(
    project_path: str,
    key: str,
    value: str,
    tags: Optional[List[str]] = None,
    append: bool = False
) -> Dict[str, Any]:
    """
    Store knowledge persistently.

    Args:
        project_path: Path to project root
        key: Unique identifier for this memory
        value: Content to store
        tags: Categories like ["pattern", "gotcha", "architecture", "config"]
        append: If True, append to existing value instead of replacing

    Returns:
        Dict with success status and memory details
    """
    memories = _load_memories(project_path)
    now = datetime.now().isoformat()

    # Find existing memory
    existing_idx = None
    for i, mem in enumerate(memories):
        if mem.get("key") == key:
            existing_idx = i
            break

    if existing_idx is not None:
        # Update existing
        existing = memories[existing_idx]
        if append:
            existing["value"] = existing.get("value", "") + "\n" + value
        else:
            existing["value"] = value
        if tags:
            # Merge tags
            existing_tags = set(existing.get("tags", []))
            existing_tags.update(tags)
            existing["tags"] = list(existing_tags)
        existing["updated_at"] = now
        action = "updated"
    else:
        # Create new
        memories.append({
            "key": key,
            "value": value,
            "tags": tags or [],
            "created_at": now,
            "updated_at": now
        })
        action = "created"

    _save_memories(project_path, memories)

    return {
        "success": True,
        "action": action,
        "key": key,
        "tags": tags or [],
        "total_memories": len(memories)
    }


async def cfa_recall(
    project_path: str,
    key: Optional[str] = None,
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Retrieve stored knowledge.

    Args:
        project_path: Path to project root
        key: Exact key to retrieve (returns single memory)
        query: Text to search in keys and values
        tags: Filter by tags (OR logic - matches any tag)
        limit: Maximum results to return

    Returns:
        Dict with matching memories
    """
    memories = _load_memories(project_path)

    if not memories:
        return {
            "success": True,
            "count": 0,
            "results": [],
            "message": "No memories stored yet. Use cfa.remember to store knowledge."
        }

    # Exact key lookup
    if key:
        for mem in memories:
            if mem.get("key") == key:
                return {
                    "success": True,
                    "count": 1,
                    "results": [mem]
                }
        return {
            "success": True,
            "count": 0,
            "results": [],
            "message": f"No memory found with key '{key}'"
        }

    # Filter by tags and/or query
    results = []
    for mem in memories:
        # Tag filter
        if tags:
            mem_tags = set(mem.get("tags", []))
            if not mem_tags.intersection(set(tags)):
                continue

        # Query filter
        if query:
            query_lower = query.lower()
            key_match = query_lower in mem.get("key", "").lower()
            value_match = query_lower in mem.get("value", "").lower()
            if not (key_match or value_match):
                continue

        results.append(mem)

    # Sort by updated_at (most recent first)
    results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    # Apply limit
    results = results[:limit]

    return {
        "success": True,
        "count": len(results),
        "total_memories": len(memories),
        "results": results
    }


async def cfa_forget(
    project_path: str,
    key: str
) -> Dict[str, Any]:
    """
    Delete a memory by key.

    Args:
        project_path: Path to project root
        key: Key of memory to delete

    Returns:
        Dict with success status
    """
    memories = _load_memories(project_path)

    original_count = len(memories)
    memories = [m for m in memories if m.get("key") != key]

    if len(memories) == original_count:
        return {
            "success": False,
            "error": f"No memory found with key '{key}'"
        }

    _save_memories(project_path, memories)

    return {
        "success": True,
        "deleted_key": key,
        "remaining_memories": len(memories)
    }
