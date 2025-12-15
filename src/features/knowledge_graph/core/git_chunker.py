"""Git Chunker - Extract COMMIT chunks from git history.

Creates KnowledgeChunks from git commits, linking them to modified code.
This enables understanding WHY code changed over time.
"""

import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from .models import KnowledgeChunk, ChunkType, ChunkEdge, EdgeType


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return len(text) // 4


class GitChunker:
    """Extract COMMIT chunks from git history."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.git_dir = project_path / ".git"

    def is_git_repo(self) -> bool:
        """Check if project is a git repository."""
        return self.git_dir.exists()

    def get_commits(
        self,
        limit: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
        path_filter: Optional[str] = None
    ) -> List[KnowledgeChunk]:
        """
        Extract COMMIT chunks from git log.

        Args:
            limit: Maximum commits to retrieve
            since: Start date (e.g., "2024-01-01", "1 week ago")
            until: End date
            path_filter: Only commits affecting this path

        Returns:
            List of KnowledgeChunk with type COMMIT
        """
        if not self.is_git_repo():
            return []

        # Build git log command
        cmd = [
            "git", "-C", str(self.project_path), "log",
            f"--max-count={limit}",
            "--format=%H|%h|%an|%ae|%ad|%s|%b|||COMMIT_END|||",
            "--date=iso-strict",
            "--name-status"
        ]

        if since:
            cmd.append(f"--since={since}")
        if until:
            cmd.append(f"--until={until}")
        if path_filter:
            cmd.extend(["--", path_filter])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path
            )
            if result.returncode != 0:
                return []

            return self._parse_git_log(result.stdout)
        except Exception:
            return []

    def _parse_git_log(self, log_output: str) -> List[KnowledgeChunk]:
        """Parse git log output into COMMIT chunks."""
        chunks = []

        # Split by commit delimiter
        commit_blocks = log_output.split("|||COMMIT_END|||")

        for block in commit_blocks:
            block = block.strip()
            if not block:
                continue

            chunk = self._parse_commit_block(block)
            if chunk:
                chunks.append(chunk)

        return chunks

    def _parse_commit_block(self, block: str) -> Optional[KnowledgeChunk]:
        """Parse a single commit block."""
        lines = block.split("\n")
        if not lines:
            return None

        # First line has metadata
        meta_line = lines[0]
        parts = meta_line.split("|")
        if len(parts) < 6:
            return None

        commit_hash = parts[0]
        short_hash = parts[1]
        author_name = parts[2]
        author_email = parts[3]
        date_str = parts[4]
        subject = parts[5]
        body = parts[6] if len(parts) > 6 else ""

        # Parse file changes
        files_changed = []
        change_types = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}

        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            # Format: M\tfilename or R100\told\tnew
            match = re.match(r'^([AMDRT]\d*)\t(.+)$', line)
            if match:
                change_type = match.group(1)[0]
                file_path = match.group(2)
                # Handle renames (R100\told\tnew)
                if "\t" in file_path:
                    old_path, new_path = file_path.split("\t", 1)
                    files_changed.append({
                        "type": "renamed",
                        "old_path": old_path,
                        "new_path": new_path
                    })
                else:
                    files_changed.append({
                        "type": change_types.get(change_type, "modified"),
                        "path": file_path
                    })

        # Build content
        content_parts = [
            f"# Commit: {short_hash}",
            f"**Author**: {author_name} <{author_email}>",
            f"**Date**: {date_str}",
            "",
            f"## {subject}",
        ]

        if body.strip():
            content_parts.extend(["", body.strip()])

        if files_changed:
            content_parts.extend(["", "## Files Changed"])
            for fc in files_changed:
                if fc["type"] == "renamed":
                    content_parts.append(f"- 🔄 {fc['old_path']} → {fc['new_path']}")
                elif fc["type"] == "added":
                    content_parts.append(f"- ➕ {fc['path']}")
                elif fc["type"] == "deleted":
                    content_parts.append(f"- ➖ {fc['path']}")
                else:
                    content_parts.append(f"- ✏️ {fc['path']}")

        content = "\n".join(content_parts)

        # Build compressed version (just subject + file list)
        compressed = f"{short_hash}: {subject}"
        if files_changed:
            file_names = [
                fc.get("path", fc.get("new_path", ""))
                for fc in files_changed[:5]
            ]
            compressed += f" [{', '.join(file_names)}"
            if len(files_changed) > 5:
                compressed += f" +{len(files_changed) - 5} more"
            compressed += "]"

        # Parse date
        try:
            updated_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            updated_at = datetime.now()

        # Store file paths in tags for edge building
        file_paths = [
            fc.get("path", fc.get("new_path", ""))
            for fc in files_changed
            if fc.get("path") or fc.get("new_path")
        ]

        return KnowledgeChunk(
            id=f"commit:{commit_hash[:12]}",
            chunk_type=ChunkType.COMMIT,
            content=content,
            content_compressed=compressed,
            token_count=estimate_tokens(content),
            token_count_compressed=estimate_tokens(compressed),
            file_path=f".git/commits/{commit_hash}",  # Virtual path
            symbol_name=short_hash,
            signature=f"{short_hash}: {subject[:50]}{'...' if len(subject) > 50 else ''}",
            created_at=updated_at,
            updated_at=updated_at,
            source="git",
            confidence=1.0,
            tags=file_paths,  # Store affected files for edge building
            extra={
                "commit_hash": commit_hash,
                "short_hash": short_hash,
                "author_name": author_name,
                "author_email": author_email,
                "subject": subject,
                "files_changed": files_changed,
                "files_count": len(files_changed)
            }
        )

    def get_file_history(
        self,
        file_path: str,
        limit: int = 20
    ) -> List[KnowledgeChunk]:
        """Get COMMIT chunks for a specific file."""
        return self.get_commits(limit=limit, path_filter=file_path)

    def get_blame_info(
        self,
        file_path: str,
        line_start: int,
        line_end: Optional[int] = None
    ) -> List[Dict]:
        """
        Get blame information for specific lines.

        Returns list of {commit_hash, author, date, line, content}
        """
        if not self.is_git_repo():
            return []

        line_end = line_end or line_start
        cmd = [
            "git", "-C", str(self.project_path), "blame",
            "-L", f"{line_start},{line_end}",
            "--porcelain",
            file_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path
            )
            if result.returncode != 0:
                return []

            return self._parse_blame(result.stdout)
        except Exception:
            return []

    def _parse_blame(self, blame_output: str) -> List[Dict]:
        """Parse git blame --porcelain output."""
        blame_info = []
        lines = blame_output.split("\n")

        current_commit = {}
        i = 0
        while i < len(lines):
            line = lines[i]

            # New commit header: hash orig_line final_line [group_lines]
            if re.match(r'^[0-9a-f]{40} ', line):
                parts = line.split()
                current_commit = {
                    "commit_hash": parts[0],
                    "original_line": int(parts[1]),
                    "final_line": int(parts[2])
                }
            elif line.startswith("author "):
                current_commit["author"] = line[7:]
            elif line.startswith("author-time "):
                timestamp = int(line[12:])
                current_commit["date"] = datetime.fromtimestamp(timestamp).isoformat()
            elif line.startswith("summary "):
                current_commit["summary"] = line[8:]
            elif line.startswith("\t"):
                # Content line
                current_commit["content"] = line[1:]
                blame_info.append(current_commit.copy())
                current_commit = {}

            i += 1

        return blame_info

    def get_diff_between(
        self,
        commit_a: str,
        commit_b: str,
        file_path: Optional[str] = None
    ) -> str:
        """Get diff between two commits."""
        if not self.is_git_repo():
            return ""

        cmd = [
            "git", "-C", str(self.project_path), "diff",
            commit_a, commit_b,
            "--unified=3"
        ]

        if file_path:
            cmd.extend(["--", file_path])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_path
            )
            return result.stdout
        except Exception:
            return ""

    def build_modified_in_edges(
        self,
        commits: List[KnowledgeChunk],
        file_chunks: Dict[str, str]
    ) -> List[ChunkEdge]:
        """
        Build MODIFIED_IN edges from code chunks to commits.

        Args:
            commits: List of COMMIT chunks
            file_chunks: Dict mapping file_path -> chunk_id

        Returns:
            List of edges (code_chunk -> commit)
        """
        edges = []

        for commit in commits:
            files_changed = commit.extra.get("files_changed", [])

            for fc in files_changed:
                file_path = fc.get("path") or fc.get("new_path")
                if not file_path:
                    continue

                # Find chunk for this file
                if file_path in file_chunks:
                    chunk_id = file_chunks[file_path]
                    edges.append(ChunkEdge(
                        source_id=chunk_id,
                        target_id=commit.id,
                        edge_type=EdgeType.MODIFIED_IN,
                        weight=1.0,
                        metadata={"change_type": fc.get("type", "modified")}
                    ))

        return edges
