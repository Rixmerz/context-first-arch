"""Timeline - Navigate through project states over time.

Captures two types of snapshots:
1. USER snapshots: Manual checkpoints by the user ("before refactoring")
2. AGENT snapshots: Automatic checkpoints by AI during work

This enables:
- Rollback to previous states
- Comparing what changed between states
- Understanding project evolution
- Recovery from mistakes
"""

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import KnowledgeChunk, ChunkType, ChunkEdge, EdgeType
from .storage import ChunkStorage


class SnapshotType(Enum):
    """Type of snapshot."""
    USER = "user"      # Manual checkpoint by human
    AGENT = "agent"    # Automatic checkpoint by AI


@dataclass
class FileState:
    """State of a single file at snapshot time."""
    path: str
    exists: bool
    size: int
    modified_at: str
    content_hash: str  # MD5 of content for change detection
    git_status: Optional[str] = None  # M, A, D, ?


@dataclass
class Snapshot:
    """A point-in-time capture of project state."""
    id: str
    snapshot_type: SnapshotType
    name: str
    description: str

    # State capture
    files: List[FileState]
    git_commit: Optional[str]  # Current HEAD at snapshot time
    git_branch: Optional[str]
    git_dirty: bool  # Uncommitted changes?

    # Context
    task_id: Optional[str]  # Active task at snapshot time
    task_goal: Optional[str]

    # Metadata
    created_at: datetime
    created_by: str  # "user" or agent name
    tags: List[str] = field(default_factory=list)

    # Lineage
    previous_snapshot_id: Optional[str] = None

    def to_chunk(self) -> KnowledgeChunk:
        """Convert to KnowledgeChunk for storage."""
        chunk_type = (
            ChunkType.SNAPSHOT_USER
            if self.snapshot_type == SnapshotType.USER
            else ChunkType.SNAPSHOT_AGENT
        )

        # Build content
        content_parts = [
            f"# Snapshot: {self.name}",
            f"**Type**: {self.snapshot_type.value}",
            f"**Created**: {self.created_at.isoformat()}",
            f"**By**: {self.created_by}",
            "",
            f"## Description",
            self.description,
            "",
        ]

        if self.git_commit:
            content_parts.extend([
                f"## Git State",
                f"- Branch: {self.git_branch}",
                f"- Commit: {self.git_commit[:8]}",
                f"- Dirty: {'Yes' if self.git_dirty else 'No'}",
                "",
            ])

        if self.task_id:
            content_parts.extend([
                f"## Active Task",
                f"- ID: {self.task_id}",
                f"- Goal: {self.task_goal}",
                "",
            ])

        # File summary
        content_parts.append(f"## Files ({len(self.files)} tracked)")
        for f in self.files[:20]:  # Limit to first 20
            status = f.git_status or "?"
            content_parts.append(f"- [{status}] {f.path}")
        if len(self.files) > 20:
            content_parts.append(f"- ... and {len(self.files) - 20} more")

        content = "\n".join(content_parts)

        # Compressed version
        compressed = (
            f"[{self.snapshot_type.value}] {self.name}: "
            f"{len(self.files)} files @ {self.git_commit[:8] if self.git_commit else 'no-git'}"
        )

        return KnowledgeChunk(
            id=f"snapshot:{self.id}",
            chunk_type=chunk_type,
            content=content,
            content_compressed=compressed,
            token_count=len(content) // 4,
            token_count_compressed=len(compressed) // 4,
            file_path=".claude/snapshots",
            symbol_name=self.name,
            signature=f"{self.snapshot_type.value}: {self.name}",
            created_at=self.created_at,
            updated_at=self.created_at,
            source=self.created_by,
            confidence=1.0,
            tags=self.tags + [self.snapshot_type.value],
            extra={
                "snapshot_id": self.id,
                "snapshot_type": self.snapshot_type.value,
                "git_commit": self.git_commit,
                "git_branch": self.git_branch,
                "git_dirty": self.git_dirty,
                "file_count": len(self.files),
                "task_id": self.task_id,
                "previous_snapshot": self.previous_snapshot_id,
            }
        )


class TimelineManager:
    """Manage project timeline with snapshots."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.storage = ChunkStorage(project_path)
        self._ensure_table()

    def _ensure_table(self):
        """Create snapshots table if not exists."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                snapshot_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                git_commit TEXT,
                git_branch TEXT,
                git_dirty INTEGER,
                task_id TEXT,
                task_goal TEXT,
                files_json TEXT,
                created_at TEXT,
                created_by TEXT,
                previous_snapshot_id TEXT,
                tags TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _get_git_state(self) -> Dict[str, Any]:
        """Get current git state."""
        git_dir = self.project_path / ".git"
        if not git_dir.exists():
            return {
                "commit": None,
                "branch": None,
                "dirty": False,
                "status": {}
            }

        result = {}

        # Get current commit
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True,
                cwd=self.project_path
            )
            result["commit"] = proc.stdout.strip() if proc.returncode == 0 else None
        except Exception:
            result["commit"] = None

        # Get current branch
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True,
                cwd=self.project_path
            )
            result["branch"] = proc.stdout.strip() if proc.returncode == 0 else None
        except Exception:
            result["branch"] = None

        # Get status (dirty check and file statuses)
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True,
                cwd=self.project_path
            )
            if proc.returncode == 0:
                status_lines = proc.stdout.strip().split("\n")
                result["dirty"] = bool(proc.stdout.strip())
                result["status"] = {}
                for line in status_lines:
                    if line:
                        status = line[:2].strip()
                        path = line[3:]
                        result["status"][path] = status
            else:
                result["dirty"] = False
                result["status"] = {}
        except Exception:
            result["dirty"] = False
            result["status"] = {}

        return result

    def _capture_files(self, patterns: List[str] = None) -> List[FileState]:
        """Capture state of project files."""
        files = []
        git_state = self._get_git_state()

        # Default patterns for CFA projects
        if patterns is None:
            patterns = [
                "**/*.py", "**/*.ts", "**/*.js", "**/*.tsx", "**/*.jsx",
                "**/*.rs", "**/*.go", "**/*.java",
                "**/*.md", "**/*.json", "**/*.yaml", "**/*.yml",
                "**/*.toml", "**/*.cfg", "**/*.ini",
            ]

        # Collect files
        all_paths = set()
        for pattern in patterns:
            for path in self.project_path.glob(pattern):
                if path.is_file() and ".git" not in str(path):
                    all_paths.add(path)

        # Build file states
        for path in sorted(all_paths):
            rel_path = str(path.relative_to(self.project_path))
            try:
                stat = path.stat()
                content = path.read_bytes()
                content_hash = hashlib.md5(content).hexdigest()

                files.append(FileState(
                    path=rel_path,
                    exists=True,
                    size=stat.st_size,
                    modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    content_hash=content_hash,
                    git_status=git_state["status"].get(rel_path),
                ))
            except Exception:
                continue

        return files

    def _get_current_task(self) -> Dict[str, Any]:
        """Get current task info from current-task.md."""
        task_file = self.project_path / ".claude" / "current-task.md"
        if not task_file.exists():
            return {"id": None, "goal": None}

        try:
            content = task_file.read_text()
            # Simple parsing - look for goal
            goal = None
            for line in content.split("\n"):
                if line.startswith("## Goal") or line.startswith("**Goal**"):
                    idx = content.index(line)
                    rest = content[idx:].split("\n", 2)
                    if len(rest) > 1:
                        goal = rest[1].strip()
                    break

            return {
                "id": hashlib.md5(content.encode()).hexdigest()[:8],
                "goal": goal
            }
        except Exception:
            return {"id": None, "goal": None}

    def _get_latest_snapshot(self) -> Optional[str]:
        """Get ID of the most recent snapshot."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return None

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT snapshot_id FROM snapshots
            ORDER BY created_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    def create_snapshot(
        self,
        name: str,
        description: str,
        snapshot_type: SnapshotType = SnapshotType.USER,
        created_by: str = "user",
        tags: List[str] = None
    ) -> Snapshot:
        """Create a new snapshot of current project state."""
        git_state = self._get_git_state()
        files = self._capture_files()
        task = self._get_current_task()

        # Generate ID
        snapshot_id = hashlib.md5(
            f"{name}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        snapshot = Snapshot(
            id=snapshot_id,
            snapshot_type=snapshot_type,
            name=name,
            description=description,
            files=files,
            git_commit=git_state["commit"],
            git_branch=git_state["branch"],
            git_dirty=git_state["dirty"],
            task_id=task["id"],
            task_goal=task["goal"],
            created_at=datetime.now(),
            created_by=created_by,
            tags=tags or [],
            previous_snapshot_id=self._get_latest_snapshot(),
        )

        self._save_snapshot(snapshot)
        return snapshot

    def _save_snapshot(self, snapshot: Snapshot):
        """Save snapshot to database and chunk storage."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Serialize files
        files_json = json.dumps([
            {
                "path": f.path,
                "exists": f.exists,
                "size": f.size,
                "modified_at": f.modified_at,
                "content_hash": f.content_hash,
                "git_status": f.git_status,
            }
            for f in snapshot.files
        ])

        cursor.execute("""
            INSERT OR REPLACE INTO snapshots (
                snapshot_id, snapshot_type, name, description,
                git_commit, git_branch, git_dirty,
                task_id, task_goal, files_json,
                created_at, created_by, previous_snapshot_id, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.id,
            snapshot.snapshot_type.value,
            snapshot.name,
            snapshot.description,
            snapshot.git_commit,
            snapshot.git_branch,
            1 if snapshot.git_dirty else 0,
            snapshot.task_id,
            snapshot.task_goal,
            files_json,
            snapshot.created_at.isoformat(),
            snapshot.created_by,
            snapshot.previous_snapshot_id,
            json.dumps(snapshot.tags),
        ))

        conn.commit()
        conn.close()

        # Save as chunk
        chunk = snapshot.to_chunk()
        self.storage.save_chunk(chunk)

        # Create PRECEDED_BY edge if there's a previous snapshot
        if snapshot.previous_snapshot_id:
            edge = ChunkEdge(
                source_id=f"snapshot:{snapshot.id}",
                target_id=f"snapshot:{snapshot.previous_snapshot_id}",
                edge_type=EdgeType.PRECEDED_BY,
                weight=1.0,
            )
            self.storage.save_edge(edge)

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Get a snapshot by ID."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return None

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM snapshots WHERE snapshot_id = ?
        """, (snapshot_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_snapshot(row)

    def _row_to_snapshot(self, row) -> Snapshot:
        """Convert database row to Snapshot."""
        files_data = json.loads(row[9]) if row[9] else []
        files = [
            FileState(
                path=f["path"],
                exists=f["exists"],
                size=f["size"],
                modified_at=f["modified_at"],
                content_hash=f["content_hash"],
                git_status=f.get("git_status"),
            )
            for f in files_data
        ]

        return Snapshot(
            id=row[0],
            snapshot_type=SnapshotType(row[1]),
            name=row[2],
            description=row[3],
            git_commit=row[4],
            git_branch=row[5],
            git_dirty=bool(row[6]),
            task_id=row[7],
            task_goal=row[8],
            files=files,
            created_at=datetime.fromisoformat(row[10]) if row[10] else datetime.now(),
            created_by=row[11],
            previous_snapshot_id=row[12],
            tags=json.loads(row[13]) if row[13] else [],
        )

    def list_snapshots(
        self,
        snapshot_type: Optional[SnapshotType] = None,
        limit: int = 20
    ) -> List[Snapshot]:
        """List snapshots with optional filtering."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        query = "SELECT * FROM snapshots WHERE 1=1"
        params = []

        if snapshot_type:
            query += " AND snapshot_type = ?"
            params.append(snapshot_type.value)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_snapshot(row) for row in rows]

    def compare_snapshots(
        self,
        snapshot_a_id: str,
        snapshot_b_id: str
    ) -> Dict[str, Any]:
        """Compare two snapshots and return differences."""
        snap_a = self.get_snapshot(snapshot_a_id)
        snap_b = self.get_snapshot(snapshot_b_id)

        if not snap_a or not snap_b:
            return {"error": "Snapshot not found"}

        # Build file maps
        files_a = {f.path: f for f in snap_a.files}
        files_b = {f.path: f for f in snap_b.files}

        all_paths = set(files_a.keys()) | set(files_b.keys())

        added = []
        removed = []
        modified = []
        unchanged = []

        for path in all_paths:
            in_a = path in files_a
            in_b = path in files_b

            if in_a and not in_b:
                removed.append(path)
            elif in_b and not in_a:
                added.append(path)
            elif files_a[path].content_hash != files_b[path].content_hash:
                modified.append(path)
            else:
                unchanged.append(path)

        return {
            "snapshot_a": {
                "id": snap_a.id,
                "name": snap_a.name,
                "created_at": snap_a.created_at.isoformat(),
            },
            "snapshot_b": {
                "id": snap_b.id,
                "name": snap_b.name,
                "created_at": snap_b.created_at.isoformat(),
            },
            "added": added,
            "removed": removed,
            "modified": modified,
            "unchanged_count": len(unchanged),
            "summary": (
                f"{len(added)} added, {len(removed)} removed, "
                f"{len(modified)} modified, {len(unchanged)} unchanged"
            ),
        }
