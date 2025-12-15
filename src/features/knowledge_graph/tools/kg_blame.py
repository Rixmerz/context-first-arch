"""
MCP Tool: kg.blame

Find out WHY specific code was written - links lines to commits.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.features.knowledge_graph import ChunkStorage, GitChunker


async def kg_blame(
    project_path: str,
    chunk_id: Optional[str] = None,
    file_path: Optional[str] = None,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    group_by_commit: bool = True
) -> Dict[str, Any]:
    """
    Get blame information - which commit wrote each line.

    Answers: "WHY was this code written? Who wrote it and when?"

    Args:
        project_path: Path to CFA project
        chunk_id: Chunk ID to blame (uses file_path and line_range)
        file_path: Direct file path
        line_start: Start line number (1-indexed)
        line_end: End line number
        group_by_commit: Group results by commit (default True)

    Returns:
        Dictionary with:
            - success: Boolean
            - blame_info: Blame data (per-line or grouped)
            - insights: Analysis of code ownership
            - summary: Human-readable summary

    Examples:
        # Blame entire chunk
        result = await kg_blame(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate"
        )

        # Blame specific lines
        result = await kg_blame(
            project_path="/projects/my-app",
            file_path="src/auth.py",
            line_start=50,
            line_end=75
        )

    Best Practice:
        Use blame to:
        1. Find who to ask about code decisions
        2. Understand commit context for code
        3. Identify code age (old = stable, new = volatile)
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

        # Resolve from chunk_id
        target_file = file_path
        start_line = line_start
        end_line = line_end

        if chunk_id and not target_file:
            storage = ChunkStorage(path)
            chunk = storage.get_chunk(chunk_id)
            if chunk:
                target_file = chunk.file_path
                if chunk.line_start and chunk.line_end:
                    start_line = start_line or chunk.line_start
                    end_line = end_line or chunk.line_end
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

        # Default to first 100 lines if no range specified
        if not start_line:
            start_line = 1
            end_line = end_line or 100

        end_line = end_line or start_line

        # Get blame info
        blame_data = git_chunker.get_blame_info(
            file_path=target_file,
            line_start=start_line,
            line_end=end_line
        )

        if not blame_data:
            return {
                "success": True,
                "file_path": target_file,
                "line_range": [start_line, end_line],
                "blame_info": [],
                "summary": "No blame information available (file may be untracked)"
            }

        # Analyze blame data
        commits_seen = {}
        authors_seen = {}
        for entry in blame_data:
            commit = entry.get("commit_hash", "")[:8]
            author = entry.get("author", "unknown")

            if commit not in commits_seen:
                commits_seen[commit] = {
                    "hash": commit,
                    "author": author,
                    "date": entry.get("date", ""),
                    "summary": entry.get("summary", ""),
                    "lines": []
                }
            commits_seen[commit]["lines"].append(entry.get("final_line"))

            if author not in authors_seen:
                authors_seen[author] = 0
            authors_seen[author] += 1

        # Build response
        if group_by_commit:
            blame_output = list(commits_seen.values())
            # Sort by most recent first (approximate by looking at dates)
            blame_output.sort(key=lambda x: x.get("date", ""), reverse=True)
        else:
            blame_output = blame_data

        # Calculate ownership percentages
        total_lines = len(blame_data)
        ownership = [
            {"author": author, "lines": count, "percentage": round(count / total_lines * 100, 1)}
            for author, count in sorted(authors_seen.items(), key=lambda x: x[1], reverse=True)
        ]

        # Generate insights
        insights = []

        # Primary owner
        if ownership:
            primary = ownership[0]
            insights.append(f"Primary author: {primary['author']} ({primary['percentage']}%)")

        # Code age analysis
        unique_commits = len(commits_seen)
        if unique_commits == 1:
            insights.append("Single commit: code written atomically")
        elif unique_commits > 5:
            insights.append(f"Evolved over {unique_commits} commits: actively maintained")

        # Build summary
        summary = (
            f"Lines {start_line}-{end_line} in {target_file}: "
            f"{unique_commits} commit(s), {len(authors_seen)} author(s)."
        )

        return {
            "success": True,
            "file_path": target_file,
            "chunk_id": chunk_id,
            "line_range": [start_line, end_line],
            "blame_info": blame_output,
            "ownership": ownership,
            "insights": insights,
            "summary": summary,
            "message": summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get blame: {str(e)}"
        }
