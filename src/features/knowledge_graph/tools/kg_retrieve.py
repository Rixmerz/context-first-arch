"""
MCP Tool: kg.retrieve

[PRIMARY] Retrieve task-relevant context with full omission transparency.
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
    [PRIMARY] Retrieve task-relevant context with full omission transparency.

    This is the main tool for loading context from the Knowledge Graph.
    It uses BM25 search + graph traversal to find relevant chunks,
    and ALWAYS tells you what was omitted and why.

    Args:
        project_path: Path to CFA project
        task: What you're trying to accomplish (natural language)
        token_budget: Maximum tokens to return (default 30000)
        include_types: Chunk types to include (e.g., ["function", "test"])
        exclude_types: Chunk types to exclude (e.g., ["log", "error"])
        include_tests: Include related test chunks (default True)
        compression: 0=full, 1=no_comments, 2=signature+docstring, 3=signature_only
        symbols: Specific symbols to prioritize (e.g., ["authenticate", "User"])
        files: Specific files to prioritize (e.g., ["src/auth.py"])
        auto_build: Auto-build graph if needed (default True)

    Returns:
        Dictionary with:
            - success: Boolean
            - context_markdown: Full context in markdown format
            - stats: {chunks_loaded, chunks_omitted, tokens_used, ...}
            - omission_summary: Human-readable omission summary
            - omission_by_type: Omissions grouped by chunk type
            - omission_by_reason: Omissions grouped by reason
            - available_expansions: What can be loaded with kg.expand
            - related_tests: Test chunk IDs for loaded code
            - related_commits: Commit chunk IDs for loaded code

    Examples:
        # Basic retrieval
        result = await kg_retrieve(
            project_path="/projects/my-app",
            task="Fix the authentication bug in the login function"
        )

        # Focused retrieval with symbols
        result = await kg_retrieve(
            project_path="/projects/my-app",
            task="Refactor user authentication",
            symbols=["authenticate", "validate_token", "User"],
            include_tests=True
        )

        # Minimal retrieval (signatures only)
        result = await kg_retrieve(
            project_path="/projects/my-app",
            task="Get overview of the project structure",
            compression=2,
            token_budget=10000
        )

    CRITICAL - Omission Transparency:
        The response ALWAYS includes what was NOT loaded.
        Check 'omission_summary' to understand what's missing.
        Use 'available_expansions' to see what can be loaded next.
        Use kg.expand to load specific omitted chunks.

    Best Practice:
        1. Start with a descriptive task
        2. Review omission_summary
        3. Use kg.expand if you need more context
        4. Use symbols/files to focus on specific areas
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
