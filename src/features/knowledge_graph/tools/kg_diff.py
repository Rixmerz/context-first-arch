"""
MCP Tool: kg.diff

Compare code between commits or versions.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, GitChunker


async def kg_diff(
    project_path: str,
    commit_a: str,
    commit_b: str = "HEAD",
    file_path: Optional[str] = None,
    chunk_id: Optional[str] = None,
    context_lines: int = 3
) -> Dict[str, Any]:
    """
    Get diff between two commits, optionally focused on a file/chunk.

    Answers: "What changed between these versions?"

    Args:
        project_path: Path to CFA project
        commit_a: First commit (older) - hash, tag, or branch
        commit_b: Second commit (newer) - defaults to HEAD
        file_path: Focus on specific file
        chunk_id: Focus on file containing this chunk
        context_lines: Lines of context around changes (default 3)

    Returns:
        Dictionary with:
            - success: Boolean
            - diff: The diff content
            - stats: Addition/deletion statistics
            - files_changed: List of changed files
            - summary: Human-readable summary

    Examples:
        # Diff between commits
        result = await kg_diff(
            project_path="/projects/my-app",
            commit_a="abc123",
            commit_b="def456"
        )

        # Diff for specific file
        result = await kg_diff(
            project_path="/projects/my-app",
            commit_a="main",
            commit_b="feature-branch",
            file_path="src/auth.py"
        )

        # Diff from last week to now
        result = await kg_diff(
            project_path="/projects/my-app",
            commit_a="HEAD~10",
            commit_b="HEAD"
        )

    Best Practice:
        Use diff to:
        1. Understand what changed in a feature branch
        2. Review modifications before merging
        3. Investigate when a bug was introduced
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

        # Resolve file from chunk_id
        target_file = file_path
        if chunk_id and not target_file:
            storage = ChunkStorage(path)
            chunk = storage.get_chunk(chunk_id)
            if chunk:
                target_file = chunk.file_path

        # Get diff
        diff = git_chunker.get_diff_between(
            commit_a=commit_a,
            commit_b=commit_b,
            file_path=target_file
        )

        if not diff:
            return {
                "success": True,
                "commit_a": commit_a,
                "commit_b": commit_b,
                "file_path": target_file,
                "diff": "",
                "stats": {"additions": 0, "deletions": 0, "files": 0},
                "summary": "No differences found between commits."
            }

        # Parse diff stats
        additions = diff.count("\n+") - diff.count("\n+++")
        deletions = diff.count("\n-") - diff.count("\n---")

        # Count files changed
        files_changed = []
        for line in diff.split("\n"):
            if line.startswith("diff --git"):
                # Extract file path: diff --git a/path b/path
                parts = line.split()
                if len(parts) >= 4:
                    file_changed = parts[2][2:]  # Remove "a/" prefix
                    files_changed.append(file_changed)

        # Build summary
        summary = (
            f"Diff {commit_a[:8]}..{commit_b[:8]}: "
            f"+{additions} -{deletions} in {len(files_changed)} file(s)."
        )
        if target_file:
            summary = f"Diff for {target_file}: +{additions} -{deletions}."

        # Truncate very large diffs
        max_diff_size = 50000  # ~50KB
        diff_truncated = False
        if len(diff) > max_diff_size:
            diff = diff[:max_diff_size]
            diff_truncated = True

        return {
            "success": True,
            "commit_a": commit_a,
            "commit_b": commit_b,
            "file_path": target_file,
            "chunk_id": chunk_id,
            "diff": diff,
            "diff_truncated": diff_truncated,
            "stats": {
                "additions": additions,
                "deletions": deletions,
                "files": len(files_changed)
            },
            "files_changed": files_changed,
            "summary": summary,
            "message": summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get diff: {str(e)}"
        }
