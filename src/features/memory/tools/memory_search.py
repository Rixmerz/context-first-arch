"""
MCP Tool: memory.search

Search project learnings in persistent memory.

RECOMMENDED: Call this tool early in tasks to check for previous decisions,
patterns, or context that may affect your current work.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.memory import MemoryStore


async def memory_search(
    project_path: str,
    query: str = "",
    tags: Optional[List[str]] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    [RECOMMENDED - EARLY IN TASK] Search for previous decisions and context.

    <RULES>
    1. CALL EARLY in tasks to check for existing decisions before making new ones
    2. Search by TAGS for category-based retrieval (architecture, bug-fix, etc.)
    3. Search by QUERY for content-based lookup
    4. REVIEW results before making decisions that might contradict prior work
    5. Use with kg.retrieve - memory for decisions, kg for code context
    </RULES>

    <WHEN_TO_USE>
    ✅ At task start - check if similar work was done before
    ✅ Before architectural decisions - find previous ADRs
    ✅ When debugging - check if bug was seen before
    ✅ When implementing - find established patterns
    ✅ Before ending session - find session summaries to continue from
    </WHEN_TO_USE>

    <COMMON_SEARCH_PATTERNS>
    Find previous architectural decisions:
        memory.search(tags=["architecture", "adr"])

    Find how bugs were fixed before:
        memory.search(query="race condition", tags=["bug-fix"])

    Find established patterns:
        memory.search(tags=["pattern"])

    Find session summaries to continue work:
        memory.search(tags=["session-summary"])

    Find all decisions about a topic:
        memory.search(query="authentication")
    </COMMON_SEARCH_PATTERNS>

    <RELATIONSHIP_WITH_OTHER_TOOLS>
    - Use BEFORE kg.retrieve → Check if prior context exists
    - Use AFTER making decisions → Store new decisions with memory.set
    - Use BEFORE ending session → Review what was accomplished
    </RELATIONSHIP_WITH_OTHER_TOOLS>

    Args:
        project_path: Path to CFA project
        query: Text to search in memory values (case-insensitive)
        tags: Tags to filter by (AND logic) - common tags:
            - "architecture" → Design decisions
            - "adr" → Architecture Decision Records
            - "bug-fix" → Bug solutions
            - "pattern" → Code patterns
            - "session-summary" → Session summaries
        limit: Maximum results (default: 50)

    Returns:
        - results: List of {key, value, tags, timestamp}
        - count: Number of results
        - stats: Memory store statistics

    <WORKFLOW>
    1. memory.search(tags=["relevant-tag"]) → Find prior decisions
    2. Review results → Don't contradict without good reason
    3. kg.retrieve(task="...") → Get code context
    4. Do work → Make decisions
    5. memory.set(key="...", value="...", tags=[...]) → Store new learnings
    </WORKFLOW>

    IMPORTANT: Previous sessions stored valuable context in memory.
    Searching first prevents repeating work or contradicting decisions.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Search memories
        store = MemoryStore(path)
        memories = store.search(query=query, tags=tags)

        # Apply limit
        limited_memories = memories[:limit]

        # Format results
        results = [
            {
                "key": m.key,
                "value": m.value,
                "timestamp": m.timestamp,
                "tags": m.tags
            }
            for m in limited_memories
        ]

        # Get stats
        stats = store.get_stats()

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "total_matches": len(memories),
            "stats": stats,
            "message": _format_message(query, tags, len(results), len(memories))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Memory search failed: {str(e)}"
        }


def _format_message(query: str, tags: Optional[List[str]], count: int, total: int) -> str:
    """Generate human-readable message."""
    search_parts = []

    if query:
        search_parts.append(f"query='{query}'")
    if tags:
        search_parts.append(f"tags={tags}")

    search_str = ", ".join(search_parts) if search_parts else "all memories"

    if count == 0:
        return f"No memories found for {search_str}"

    if count == total:
        return f"Found {count} memory/ies for {search_str}"
    else:
        return f"Found {count}/{total} memories for {search_str} (limited)"
