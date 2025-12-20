"""
MCP Tool: memory.set

[PRIMARY] Store project learnings in persistent memory.

OBLIGATORY: This tool MUST be called whenever you make a significant decision,
discover an important pattern, or complete a notable implementation. Without it,
future sessions will lack critical context about what was decided and why.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.memory import MemoryStore


async def memory_set(
    project_path: str,
    key: str,
    value: str,
    tags: Optional[List[str]] = None,
    append: bool = False
) -> Dict[str, Any]:
    """
    [OBLIGATORY - AFTER DECISIONS] Store decisions and learnings in persistent memory.

    <RULES>
    1. ALWAYS call memory.set after making an ARCHITECTURAL DECISION
    2. ALWAYS call memory.set after resolving a SIGNIFICANT BUG and recording the solution
    3. ALWAYS call memory.set when you establish a NEW PATTERN in the codebase
    4. ALWAYS call memory.set at the end of a task to record WHAT WAS ACCOMPLISHED
    5. Use DESCRIPTIVE keys following "topic-subtopic" format
    6. Use CONSISTENT tags for categorization (architecture, bug-fix, pattern, decision)
    7. Include the REASONING behind decisions, not just what was decided
    </RULES>

    <WHEN_TO_USE>
    ✅ After deciding on an architectural approach (e.g., "chose JWT over sessions")
    ✅ After fixing a non-obvious bug (e.g., "race condition in payment processing")
    ✅ After establishing a code pattern (e.g., "all API endpoints use ResultType")
    ✅ After completing a significant implementation milestone
    ✅ When you discover something that future sessions should know
    ✅ Before ending a session - summarize what was done
    </WHEN_TO_USE>

    <WHEN_NOT_TO_USE>
    ❌ For trivial changes (typos, formatting)
    ❌ For temporary debugging notes
    ❌ For information already in code comments
    ❌ For duplicating existing memories
    </WHEN_NOT_TO_USE>

    <MEMORY_FORMAT_PATTERNS>
    For ARCHITECTURAL DECISIONS (use ADR format):
        key: "adr-001-authentication-approach"
        value: |
            # ADR-001: JWT Authentication
            ## Context: Needed stateless auth for microservices
            ## Decision: Use JWT with refresh tokens
            ## Alternatives: Sessions (rejected: not stateless)
            ## Consequences: Must handle token refresh client-side
        tags: ["architecture", "adr", "authentication"]

    For BUG FIXES:
        key: "bug-fix-payment-race-condition"
        value: |
            ## Problem: Double charges on slow networks
            ## Root Cause: Missing idempotency key validation
            ## Solution: Added unique constraint + retry logic
            ## Files Changed: payment.ts, checkout.ts
        tags: ["bug-fix", "payment"]

    For PATTERNS:
        key: "pattern-error-handling"
        value: |
            ## Pattern: ResultType for all operations
            ## Usage: return Result.ok(data) or Result.err(error)
            ## Rationale: Explicit error handling, no exceptions
        tags: ["pattern", "error-handling"]

    For SESSION SUMMARIES:
        key: "session-summary-2024-01-15"
        value: |
            ## Completed: User authentication feature
            ## Decisions: JWT with 24h expiry
            ## Pending: Add refresh token logic
        tags: ["session-summary"]
    </MEMORY_FORMAT_PATTERNS>

    <RECOMMENDED_TAGS>
    - "architecture" → Design decisions
    - "adr" → Architecture Decision Records
    - "bug-fix" → Bug solutions
    - "pattern" → Code patterns
    - "decision" → General decisions
    - "implementation" → Implementation notes
    - "session-summary" → End-of-session summaries
    - "objective" → Goal tracking
    </RECOMMENDED_TAGS>

    Args:
        project_path: Path to CFA project
        key: Unique identifier - use "topic-subtopic" format (REQUIRED)
        value: Content to store - include reasoning! (REQUIRED)
        tags: List of tags for categorization (RECOMMENDED)
        append: If True, append to existing memory instead of replace

    Returns:
        - success: Boolean
        - key: Memory key
        - mode: "create", "replace", or "append"
        - timestamp: When stored

    <WORKFLOW>
    1. Make decision or complete significant work
    2. memory.set(key="descriptive-key", value="what + why", tags=[...])
    3. Future sessions can find this with memory.search(tags=[...])
    </WORKFLOW>

    CRITICAL: Memories are how you maintain context across sessions.
    Without memory.set, future sessions start from scratch every time.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Validate inputs
        if not key or not key.strip():
            return {"success": False, "error": "Memory key cannot be empty"}

        if not value or not value.strip():
            return {"success": False, "error": "Memory value cannot be empty"}

        # Initialize store
        store = MemoryStore(path)
        key = key.strip()
        value = value.strip()
        tags = tags or []

        # Check if memory exists
        existing = store.get(key)

        if existing and append:
            # Append mode - use edit with append
            updated = store.edit(
                key=key,
                new_value=value,
                new_tags=tags if tags else None,
                append=True
            )

            if not updated:
                return {
                    "success": False,
                    "error": f"Failed to append to memory: {key}"
                }

            return {
                "success": True,
                "key": updated.key,
                "timestamp": updated.timestamp,
                "tags": updated.tags,
                "mode": "append",
                "previous_value": existing.value[:200] + ("..." if len(existing.value) > 200 else ""),
                "new_value": updated.value[:200] + ("..." if len(updated.value) > 200 else ""),
                "message": f"Appended to memory '{key}'"
            }

        elif existing:
            # Replace mode - update existing
            updated = store.edit(
                key=key,
                new_value=value,
                new_tags=tags if tags else None,
                append=False
            )

            if not updated:
                return {
                    "success": False,
                    "error": f"Failed to update memory: {key}"
                }

            return {
                "success": True,
                "key": updated.key,
                "timestamp": updated.timestamp,
                "tags": updated.tags,
                "mode": "replace",
                "previous_value": existing.value[:200] + ("..." if len(existing.value) > 200 else ""),
                "message": f"Updated memory '{key}'" + (f" with tags: {', '.join(updated.tags)}" if updated.tags else "")
            }

        else:
            # Create new memory
            memory = store.set(key=key, value=value, tags=tags)

            return {
                "success": True,
                "key": memory.key,
                "timestamp": memory.timestamp,
                "tags": memory.tags,
                "mode": "create",
                "message": f"Created memory '{key}'" + (f" with tags: {', '.join(memory.tags)}" if memory.tags else "")
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to store memory: {str(e)}"
        }
