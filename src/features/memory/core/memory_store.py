"""
Persistent memory store for Context-First Architecture projects.

Stores project learnings, decisions, and context using SQLite.
"""

import sqlite3
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Memory:
    """Represents a stored memory."""
    key: str
    value: str
    timestamp: str
    tags: List[str]
    project_path: str


class MemoryStore:
    """SQLite-based memory store for project knowledge."""

    def __init__(self, project_path: Path):
        """
        Initialize memory store.

        Args:
            project_path: Root path of the CFA project
        """
        self.project_path = project_path
        self.db_path = project_path / ".claude" / "memory.db"
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        # Ensure .claude directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                project_path TEXT NOT NULL
            )
        """)

        # Create index on tags for faster search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
        """)

        conn.commit()
        conn.close()

    def set(self, key: str, value: str, tags: Optional[List[str]] = None) -> Memory:
        """
        Store or update a memory.

        Args:
            key: Unique identifier for the memory
            value: Content to store
            tags: Optional list of tags for categorization

        Returns:
            Memory object
        """
        tags = tags or []
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO memories (key, value, timestamp, tags, project_path)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value, timestamp, json.dumps(tags), str(self.project_path)))

        conn.commit()
        conn.close()

        return Memory(
            key=key,
            value=value,
            timestamp=timestamp,
            tags=tags,
            project_path=str(self.project_path)
        )

    def get(self, key: str) -> Optional[Memory]:
        """
        Retrieve a memory by key.

        Args:
            key: Memory identifier

        Returns:
            Memory object if found, None otherwise
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key, value, timestamp, tags, project_path
            FROM memories
            WHERE key = ?
        """, (key,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return Memory(
                key=row[0],
                value=row[1],
                timestamp=row[2],
                tags=json.loads(row[3]) if row[3] else [],
                project_path=row[4]
            )

        return None

    def search(self, query: str = "", tags: Optional[List[str]] = None) -> List[Memory]:
        """
        Search memories by query and/or tags.

        Args:
            query: Text to search in values (case-insensitive)
            tags: List of tags to filter by (AND logic - must have all tags)

        Returns:
            List of matching Memory objects
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Build query
        sql = "SELECT key, value, timestamp, tags, project_path FROM memories WHERE 1=1"
        params = []

        if query:
            sql += " AND value LIKE ?"
            params.append(f"%{query}%")

        if tags:
            # Filter by tags (all tags must be present)
            for tag in tags:
                sql += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')

        sql += " ORDER BY timestamp DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        memories = []
        for row in rows:
            memories.append(Memory(
                key=row[0],
                value=row[1],
                timestamp=row[2],
                tags=json.loads(row[3]) if row[3] else [],
                project_path=row[4]
            ))

        return memories

    def delete(self, key: str) -> bool:
        """
        Delete a memory.

        Args:
            key: Memory identifier

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM memories WHERE key = ?", (key,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def edit(
        self,
        key: str,
        new_value: Optional[str] = None,
        new_tags: Optional[List[str]] = None,
        append: bool = False
    ) -> Optional[Memory]:
        """
        Edit an existing memory.

        Args:
            key: Memory identifier
            new_value: New value (replaces or appends based on append flag)
            new_tags: New tags (replaces existing tags)
            append: If True, append new_value to existing value

        Returns:
            Updated Memory object if found, None otherwise
        """
        # Get existing memory
        existing = self.get(key)
        if not existing:
            return None

        # Prepare updated values
        if new_value is not None:
            if append:
                value = existing.value + "\n" + new_value
            else:
                value = new_value
        else:
            value = existing.value

        tags = new_tags if new_tags is not None else existing.tags
        timestamp = datetime.now().isoformat()

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE memories
            SET value = ?, timestamp = ?, tags = ?
            WHERE key = ?
        """, (value, timestamp, json.dumps(tags), key))

        conn.commit()
        conn.close()

        return Memory(
            key=key,
            value=value,
            timestamp=timestamp,
            tags=tags,
            project_path=str(self.project_path)
        )

    def list_all(self, limit: int = 100) -> List[Memory]:
        """
        List all memories.

        Args:
            limit: Maximum number of memories to return

        Returns:
            List of Memory objects
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key, value, timestamp, tags, project_path
            FROM memories
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        memories = []
        for row in rows:
            memories.append(Memory(
                key=row[0],
                value=row[1],
                timestamp=row[2],
                tags=json.loads(row[3]) if row[3] else [],
                project_path=row[4]
            ))

        return memories

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory store statistics.

        Returns:
            Dictionary with stats
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        total = cursor.fetchone()[0]

        # Get all tags
        cursor.execute("SELECT tags FROM memories WHERE tags IS NOT NULL")
        all_tags = []
        for row in cursor.fetchall():
            if row[0]:
                all_tags.extend(json.loads(row[0]))

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        conn.close()

        return {
            "total_memories": total,
            "unique_tags": len(tag_counts),
            "tag_counts": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
