"""
MCP Tool: kg.history

Get commits that modified a specific chunk or file.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, GitChunker, ChunkType


async def kg_history(
    project_path: str,
    chunk_id: Optional[str] = None,
    file_path: Optional[str] = None,
    limit: int = 20,
    since: Optional[str] = None,
    include_diff: bool = False
) -> Dict[str, Any]:
    """
    Get git history for a chunk or file.

    Answers: "What commits changed this code?"

    Args:
        project_path: Path to CFA project
        chunk_id: Chunk ID to get history for (uses file_path from chunk)
        file_path: Direct file path (alternative to chunk_id)
        limit: Maximum commits to return (default 20)
        since: Only commits since this date (e.g., "2024-01-01", "1 week ago")
        include_diff: Include diff content for each commit

    Returns:
        Dictionary with:
            - success: Boolean
            - commits: List of commit info
            - file_path: The file being tracked
            - summary: Human-readable summary

    Examples:
        # Get history for a chunk
        result = await kg_history(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate"
        )

        # Get history for a file directly
        result = await kg_history(
            project_path="/projects/my-app",
            file_path="src/auth.py",
            limit=10
        )

        # Get recent history with diffs
        result = await kg_history(
            project_path="/projects/my-app",
            file_path="src/database.py",
            since="1 month ago",
            include_diff=True
        )

    Best Practice:
        Use this to understand:
        1. How often code changes (stability)
        2. Who works on this code (ownership)
        3. Why it changed (commit messages as documentation)
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        git_chunker = GitChunker(path)

        if not git_chunker.is_git_repo():
            return {
                "success": False,
                "error": "Not a git repository"
            }

        # Resolve file path from chunk_id if provided
        target_file = file_path
        if chunk_id and not target_file:
            storage = ChunkStorage(path)
            chunk = storage.get_chunk(chunk_id)
            if chunk:
                target_file = chunk.file_path
            else:
                return {
                    "success": False,
                    "error": f"Chunk not found: {chunk_id}"
                }

        if not target_file:
            return {
                "success": False,
                "error": "Either chunk_id or file_path is required"
            }

        # Get commit history
        commits = git_chunker.get_file_history(
            file_path=target_file,
            limit=limit
        )

        # Filter by date if specified
        if since:
            # The git command already handles since, but we got all commits
            # Re-fetch with since parameter
            commits = git_chunker.get_commits(
                limit=limit,
                since=since,
                path_filter=target_file
            )

        # Build response
        commit_list = []
        for commit in commits:
            meta = commit.extra
            commit_info = {
                "hash": meta.get("commit_hash", ""),
                "short_hash": meta.get("short_hash", ""),
                "author": meta.get("author_name", ""),
                "date": commit.updated_at.isoformat() if commit.updated_at else "",
                "subject": meta.get("subject", ""),
                "files_changed": meta.get("files_count", 0)
            }

            if include_diff:
                # Get diff for this specific file in this commit
                diff = git_chunker.get_diff_between(
                    f"{meta.get('commit_hash')}^",
                    meta.get("commit_hash", ""),
                    file_path=target_file
                )
                commit_info["diff"] = diff[:2000] if len(diff) > 2000 else diff

            commit_list.append(commit_info)

        # Build summary
        if commit_list:
            authors = list(set(c["author"] for c in commit_list))
            summary = (
                f"Found {len(commit_list)} commits for {target_file}. "
                f"Contributors: {', '.join(authors[:3])}"
                f"{' +' + str(len(authors) - 3) + ' more' if len(authors) > 3 else ''}."
            )
        else:
            summary = f"No commits found for {target_file}."

        return {
            "success": True,
            "file_path": target_file,
            "chunk_id": chunk_id,
            "commit_count": len(commit_list),
            "commits": commit_list,
            "summary": summary,
            "message": summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get history: {str(e)}"
        }
