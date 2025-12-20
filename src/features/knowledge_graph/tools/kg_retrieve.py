"""
MCP Tool: kg.retrieve

[PRIMARY] Retrieve task-relevant context with full omission transparency.

OBLIGATORY: This tool MUST be called at the START of EVERY task to obtain
project context. Without it, you have NO visibility into the codebase.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import retrieve_context, ChunkStorage, GraphBuilder


async def kg_retrieve(
    project_path: str,
    task: str,
    token_budget: int = 30000,
    include_types: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None,
    include_tests: bool = True,
    compression: int = 0,
    symbols: Optional[List[str]] = None,
    files: Optional[List[str]] = None,
    auto_build: bool = True
) -> Dict[str, Any]:
    """
    [OBLIGATORY - FIRST CALL] Retrieve task-relevant context from Knowledge Graph.

    <RULES>
    1. ALWAYS call kg.retrieve FIRST before any other action on a new task
    2. DO NOT attempt to write or modify code without first calling this tool
    3. DO NOT assume you know the codebase structure without calling this tool
    4. Call with a DESCRIPTIVE task parameter that explains your intent
    5. After receiving context, REVIEW omission_summary before proceeding
    6. Use kg.expand if critical files were omitted due to token budget
    7. For follow-up questions in same task, you may skip if context is fresh
    </RULES>

    <WHEN_TO_USE>
    ✅ ALWAYS at the START of a new task or user request
    ✅ When user asks about code you haven't seen yet
    ✅ When debugging - get full context of affected modules
    ✅ When implementing features - understand existing patterns
    ✅ After long conversations - refresh context if needed
    </WHEN_TO_USE>

    <WHEN_NOT_TO_USE>
    ❌ When context was just retrieved in the same turn
    ❌ For simple follow-up questions about already-loaded code
    ❌ When user explicitly provides all needed code in their message
    </WHEN_NOT_TO_USE>

    <GOOD_TASK_EXAMPLES>
    ✓ "Understand the authentication flow and how JWT tokens are validated"
    ✓ "Find all API endpoints related to user management"
    ✓ "Debug the payment processing error in checkout"
    ✓ "Refactor the database connection handling"
    </GOOD_TASK_EXAMPLES>

    <BAD_TASK_EXAMPLES>
    ✗ "code" (too vague - won't find relevant context)
    ✗ "everything" (wastes token budget)
    ✗ "fix bug" (doesn't specify which bug or area)
    </BAD_TASK_EXAMPLES>

    Args:
        project_path: Path to CFA project (REQUIRED)
        task: What you're trying to accomplish - BE SPECIFIC (REQUIRED)
        token_budget: Maximum tokens to return (default 30000)
            - Use 15000-20000 for focused tasks
            - Use 25000-30000 for broad exploration
        include_types: Chunk types to include (e.g., ["function", "class", "test"])
        exclude_types: Chunk types to exclude (e.g., ["log", "comment"])
        include_tests: Include related test chunks (default True)
        compression: Compression level:
            - 0 = full code (default)
            - 1 = no comments
            - 2 = signature + docstring only
            - 3 = signature only
        symbols: Specific symbols to prioritize (e.g., ["authenticate", "User"])
        files: Specific files to prioritize (e.g., ["src/auth.py"])
        auto_build: Auto-build graph if needed (default True)

    Returns:
        - context_markdown: Full context in markdown format (USE THIS)
        - omission_summary: What was NOT loaded (CHECK THIS)
        - available_expansions: Omitted chunks you can load with kg.expand
        - stats: {chunks_loaded, chunks_omitted, tokens_used}
        - related_tests: Test IDs for loaded code

    <WORKFLOW>
    1. kg.retrieve(task="your descriptive task") → Get initial context
    2. Check omission_summary → See what's missing
    3. If critical code was omitted → Use kg.expand(chunk_ids=[...])
    4. Now you have visibility → Proceed with implementation
    5. If you make significant decisions → Use memory.set to record them
    </WORKFLOW>

    CRITICAL: Without calling kg.retrieve first, you are operating BLIND.
    You will miss important code, patterns, and dependencies.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Auto-build graph if needed
        if auto_build:
            db_path = path / ".claude" / "knowledge_graph.db"
            if not db_path.exists():
                storage = ChunkStorage(path)
                builder = GraphBuilder(path, storage)
                builder.build_graph()

        # Retrieve context
        result = await retrieve_context(
            project_path=str(path),
            task=task,
            token_budget=token_budget,
            include_types=include_types,
            exclude_types=exclude_types,
            include_tests=include_tests,
            compression=compression,
            symbols=symbols,
            files=files,
        )

        return result

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve context: {str(e)}"
        }
