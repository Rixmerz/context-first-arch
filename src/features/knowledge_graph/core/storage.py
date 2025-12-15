"""
SQLite Storage for Project Knowledge Graph.

Persists chunks and edges with FTS5 full-text search support.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from .models import (
    ChunkEdge,
    ChunkType,
    EdgeType,
    GraphStats,
    KnowledgeChunk,
)


class ChunkStorage:
    """
    SQLite-based storage for the Project Knowledge Graph.

    Features:
    - FTS5 full-text search for content
    - Efficient chunk and edge storage
    - Graph statistics tracking
    - Incremental updates
    """

    def __init__(self, project_path: Path):
        """
        Initialize chunk storage.

        Args:
            project_path: Root path of the CFA project
        """
        self.project_path = project_path
        self.db_path = project_path / ".claude" / "knowledge_graph.db"
        self._init_db()

    def _init_db(self):
        """Initialize database schema with FTS5."""
        # Ensure .claude directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # === CHUNKS TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    chunk_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_compressed TEXT,
                    token_count INTEGER DEFAULT 0,
                    token_count_compressed INTEGER DEFAULT 0,
                    file_path TEXT,
                    line_start INTEGER,
                    line_end INTEGER,
                    symbol_name TEXT,
                    signature TEXT,
                    docstring TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT DEFAULT 'auto',
                    confidence REAL DEFAULT 1.0,
                    feature TEXT,
                    tags TEXT,
                    extra TEXT
                )
            """)

            # === EDGES TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    metadata TEXT,
                    PRIMARY KEY (source_id, target_id, edge_type)
                )
            """)

            # === GRAPH METADATA TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # === FTS5 VIRTUAL TABLE FOR SEARCH ===
            # Check if FTS table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='chunks_fts'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE VIRTUAL TABLE chunks_fts USING fts5(
                        chunk_id,
                        content,
                        symbol_name,
                        file_path,
                        content='chunks',
                        content_rowid='rowid'
                    )
                """)

                # Triggers to keep FTS in sync
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                        INSERT INTO chunks_fts(rowid, chunk_id, content, symbol_name, file_path)
                        VALUES (new.rowid, new.chunk_id, new.content, new.symbol_name, new.file_path);
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, content, symbol_name, file_path)
                        VALUES ('delete', old.rowid, old.chunk_id, old.content, old.symbol_name, old.file_path);
                    END
                """)

                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                        INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, content, symbol_name, file_path)
                        VALUES ('delete', old.rowid, old.chunk_id, old.content, old.symbol_name, old.file_path);
                        INSERT INTO chunks_fts(rowid, chunk_id, content, symbol_name, file_path)
                        VALUES (new.rowid, new.chunk_id, new.content, new.symbol_name, new.file_path);
                    END
                """)

            # === INDEXES ===
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_file
                ON chunks(file_path)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_type
                ON chunks(chunk_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_symbol
                ON chunks(symbol_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_feature
                ON chunks(feature)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_source
                ON edges(source_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_target
                ON edges(target_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_type
                ON edges(edge_type)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # === CHUNK OPERATIONS ===

    def save_chunk(self, chunk: KnowledgeChunk) -> bool:
        """
        Save or update a chunk.

        Args:
            chunk: KnowledgeChunk to save

        Returns:
            True if successful
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if chunk exists
            cursor.execute("SELECT rowid FROM chunks WHERE chunk_id = ?", (chunk.id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing chunk
                cursor.execute("""
                    UPDATE chunks SET
                        chunk_type = ?, content = ?, content_compressed = ?,
                        token_count = ?, token_count_compressed = ?,
                        file_path = ?, line_start = ?, line_end = ?, symbol_name = ?,
                        signature = ?, docstring = ?,
                        updated_at = ?, source = ?, confidence = ?,
                        feature = ?, tags = ?, extra = ?
                    WHERE chunk_id = ?
                """, (
                    chunk.chunk_type.value,
                    chunk.content,
                    chunk.content_compressed,
                    chunk.token_count,
                    chunk.token_count_compressed,
                    chunk.file_path,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.symbol_name,
                    chunk.signature,
                    chunk.docstring,
                    datetime.now().isoformat(),
                    chunk.source,
                    chunk.confidence,
                    chunk.feature,
                    json.dumps(chunk.tags),
                    json.dumps(chunk.extra),
                    chunk.id,
                ))
            else:
                # Insert new chunk
                cursor.execute("""
                    INSERT INTO chunks (
                        chunk_id, chunk_type, content, content_compressed,
                        token_count, token_count_compressed,
                        file_path, line_start, line_end, symbol_name,
                        signature, docstring,
                        created_at, updated_at, source, confidence,
                        feature, tags, extra
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk.id,
                    chunk.chunk_type.value,
                    chunk.content,
                    chunk.content_compressed,
                    chunk.token_count,
                    chunk.token_count_compressed,
                    chunk.file_path,
                    chunk.line_start,
                    chunk.line_end,
                    chunk.symbol_name,
                    chunk.signature,
                    chunk.docstring,
                    chunk.created_at,
                    datetime.now().isoformat(),
                    chunk.source,
                    chunk.confidence,
                    chunk.feature,
                    json.dumps(chunk.tags),
                    json.dumps(chunk.extra),
                ))

            conn.commit()
            return True

    def save_chunks(self, chunks: List[KnowledgeChunk]) -> int:
        """
        Batch save multiple chunks.

        Args:
            chunks: List of chunks to save

        Returns:
            Number of chunks saved
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            data = [
                (
                    c.id, c.chunk_type.value, c.content, c.content_compressed,
                    c.token_count, c.token_count_compressed,
                    c.file_path, c.line_start, c.line_end, c.symbol_name,
                    c.signature, c.docstring,
                    c.created_at, now, c.source, c.confidence,
                    c.feature, json.dumps(c.tags), json.dumps(c.extra)
                )
                for c in chunks
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO chunks (
                    chunk_id, chunk_type, content, content_compressed,
                    token_count, token_count_compressed,
                    file_path, line_start, line_end, symbol_name,
                    signature, docstring,
                    created_at, updated_at, source, confidence,
                    feature, tags, extra
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            # Rebuild FTS index to fix rowid gaps from INSERT OR REPLACE
            cursor.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")

            conn.commit()
            return len(chunks)

    def get_chunk(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """
        Get a chunk by ID.

        Args:
            chunk_id: Unique chunk identifier

        Returns:
            KnowledgeChunk if found, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE chunk_id = ?",
                (chunk_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_chunk(row)
            return None

    def get_chunks(self, chunk_ids: List[str]) -> List[KnowledgeChunk]:
        """
        Get multiple chunks by IDs.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            List of found chunks
        """
        if not chunk_ids:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(chunk_ids))
            cursor.execute(
                f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})",
                chunk_ids
            )

            return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def get_chunks_by_type(
        self,
        chunk_type: ChunkType,
        limit: int = 100
    ) -> List[KnowledgeChunk]:
        """Get all chunks of a specific type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE chunk_type = ? LIMIT ?",
                (chunk_type.value, limit)
            )

            return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def get_chunks_by_file(self, file_path: str) -> List[KnowledgeChunk]:
        """Get all chunks from a specific file."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE file_path = ? ORDER BY line_start",
                (file_path,)
            )

            return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def get_chunks_by_feature(self, feature: str) -> List[KnowledgeChunk]:
        """Get all chunks belonging to a feature."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE feature = ?",
                (feature,)
            )

            return [self._row_to_chunk(row) for row in cursor.fetchall()]

    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk and its edges."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete edges
            cursor.execute(
                "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
                (chunk_id, chunk_id)
            )

            # Delete chunk
            cursor.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))

            conn.commit()
            return cursor.rowcount > 0

    def delete_chunks_by_file(self, file_path: str) -> int:
        """Delete all chunks from a file (for incremental updates)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get chunk IDs first
            cursor.execute(
                "SELECT chunk_id FROM chunks WHERE file_path = ?",
                (file_path,)
            )
            chunk_ids = [row[0] for row in cursor.fetchall()]

            if chunk_ids:
                placeholders = ",".join("?" * len(chunk_ids))

                # Delete edges
                cursor.execute(
                    f"DELETE FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    chunk_ids + chunk_ids
                )

                # Delete chunks
                cursor.execute(
                    f"DELETE FROM chunks WHERE chunk_id IN ({placeholders})",
                    chunk_ids
                )

            conn.commit()
            return len(chunk_ids)

    # === EDGE OPERATIONS ===

    def save_edge(self, edge: ChunkEdge) -> bool:
        """Save or update an edge."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO edges (
                    source_id, target_id, edge_type, weight, metadata
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                edge.source_id,
                edge.target_id,
                edge.edge_type.value,
                edge.weight,
                json.dumps(edge.metadata),
            ))

            conn.commit()
            return True

    def save_edges(self, edges: List[ChunkEdge]) -> int:
        """Batch save multiple edges."""
        if not edges:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            data = [
                (e.source_id, e.target_id, e.edge_type.value, e.weight, json.dumps(e.metadata))
                for e in edges
            ]

            cursor.executemany("""
                INSERT OR REPLACE INTO edges (
                    source_id, target_id, edge_type, weight, metadata
                ) VALUES (?, ?, ?, ?, ?)
            """, data)

            conn.commit()
            return len(edges)

    def get_edges_from(
        self,
        source_id: str,
        edge_type: Optional[EdgeType] = None
    ) -> List[ChunkEdge]:
        """Get all edges from a source chunk."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if edge_type:
                cursor.execute(
                    "SELECT * FROM edges WHERE source_id = ? AND edge_type = ?",
                    (source_id, edge_type.value)
                )
            else:
                cursor.execute(
                    "SELECT * FROM edges WHERE source_id = ?",
                    (source_id,)
                )

            return [self._row_to_edge(row) for row in cursor.fetchall()]

    def get_edges_to(
        self,
        target_id: str,
        edge_type: Optional[EdgeType] = None
    ) -> List[ChunkEdge]:
        """Get all edges pointing to a target chunk."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if edge_type:
                cursor.execute(
                    "SELECT * FROM edges WHERE target_id = ? AND edge_type = ?",
                    (target_id, edge_type.value)
                )
            else:
                cursor.execute(
                    "SELECT * FROM edges WHERE target_id = ?",
                    (target_id,)
                )

            return [self._row_to_edge(row) for row in cursor.fetchall()]

    # === SEARCH OPERATIONS (FTS5) ===

    def search_content(
        self,
        query: str,
        chunk_types: Optional[List[ChunkType]] = None,
        limit: int = 50
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Full-text search using FTS5 with BM25 ranking.

        Args:
            query: Search query
            chunk_types: Optional filter by types
            limit: Maximum results

        Returns:
            List of (chunk, score) tuples sorted by relevance
        """
        # Guard against empty queries (FTS5 doesn't support empty MATCH)
        if not query or not query.strip():
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # FTS5 search with BM25 scoring
            if chunk_types:
                type_values = [t.value for t in chunk_types]
                placeholders = ",".join("?" * len(type_values))
                cursor.execute(f"""
                    SELECT c.*, bm25(chunks_fts) as score
                    FROM chunks c
                    JOIN chunks_fts ON c.chunk_id = chunks_fts.chunk_id
                    WHERE chunks_fts MATCH ?
                    AND c.chunk_type IN ({placeholders})
                    ORDER BY score
                    LIMIT ?
                """, (query, *type_values, limit))
            else:
                cursor.execute("""
                    SELECT c.*, bm25(chunks_fts) as score
                    FROM chunks c
                    JOIN chunks_fts ON c.chunk_id = chunks_fts.chunk_id
                    WHERE chunks_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                """, (query, limit))

            results = []
            for row in cursor.fetchall():
                chunk = self._row_to_chunk(row)
                # BM25 returns negative scores, closer to 0 is better
                score = -row["score"] if row["score"] else 0
                results.append((chunk, score))

            return results

    def search_symbol(
        self,
        symbol_name: str,
        exact: bool = False
    ) -> List[KnowledgeChunk]:
        """Search chunks by symbol name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if exact:
                cursor.execute(
                    "SELECT * FROM chunks WHERE symbol_name = ?",
                    (symbol_name,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM chunks WHERE symbol_name LIKE ?",
                    (f"%{symbol_name}%",)
                )

            return [self._row_to_chunk(row) for row in cursor.fetchall()]

    # === STATISTICS ===

    def get_stats(self) -> GraphStats:
        """Get Knowledge Graph statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total chunks
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]

            # Total edges
            cursor.execute("SELECT COUNT(*) FROM edges")
            total_edges = cursor.fetchone()[0]

            # Chunks by type
            cursor.execute("""
                SELECT chunk_type, COUNT(*) as count
                FROM chunks
                GROUP BY chunk_type
            """)
            chunks_by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Edges by type
            cursor.execute("""
                SELECT edge_type, COUNT(*) as count
                FROM edges
                GROUP BY edge_type
            """)
            edges_by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Total tokens
            cursor.execute("SELECT SUM(token_count) FROM chunks")
            total_tokens = cursor.fetchone()[0] or 0

            # Last build time
            cursor.execute(
                "SELECT value FROM graph_metadata WHERE key = 'last_build'"
            )
            row = cursor.fetchone()
            last_build = row[0] if row else ""

            # Last file change
            cursor.execute(
                "SELECT value FROM graph_metadata WHERE key = 'last_file_change'"
            )
            row = cursor.fetchone()
            last_file_change = row[0] if row else ""

            # Check if rebuild needed
            needs_rebuild = last_file_change > last_build if last_build and last_file_change else True

            return GraphStats(
                total_chunks=total_chunks,
                total_edges=total_edges,
                chunks_by_type=chunks_by_type,
                edges_by_type=edges_by_type,
                total_tokens=total_tokens,
                last_build=last_build,
                last_file_change=last_file_change,
                needs_rebuild=needs_rebuild,
            )

    def set_metadata(self, key: str, value: str):
        """Set a metadata value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO graph_metadata (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """Get a metadata value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM graph_metadata WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def mark_build_complete(self):
        """Mark the current build as complete."""
        self.set_metadata("last_build", datetime.now().isoformat())

    def mark_file_changed(self):
        """Mark that files have changed (triggers rebuild)."""
        self.set_metadata("last_file_change", datetime.now().isoformat())

    # === CLEAR/RESET ===

    def clear_all(self):
        """Clear all data from the Knowledge Graph."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM edges")
            cursor.execute("DELETE FROM graph_metadata")
            # Rebuild FTS index to ensure consistency
            cursor.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            conn.commit()

    def clear_chunks_by_type(self, chunk_type: ChunkType) -> int:
        """Clear all chunks of a specific type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get chunk IDs first
            cursor.execute(
                "SELECT chunk_id FROM chunks WHERE chunk_type = ?",
                (chunk_type.value,)
            )
            chunk_ids = [row[0] for row in cursor.fetchall()]

            if chunk_ids:
                placeholders = ",".join("?" * len(chunk_ids))

                # Delete edges
                cursor.execute(
                    f"DELETE FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    chunk_ids + chunk_ids
                )

                # Delete chunks
                cursor.execute(
                    f"DELETE FROM chunks WHERE chunk_id IN ({placeholders})",
                    chunk_ids
                )

            conn.commit()
            return len(chunk_ids)

    # === INTERNAL HELPERS ===

    def _row_to_chunk(self, row: sqlite3.Row) -> KnowledgeChunk:
        """Convert database row to KnowledgeChunk."""
        return KnowledgeChunk(
            id=row["chunk_id"],
            chunk_type=ChunkType(row["chunk_type"]),
            content=row["content"],
            content_compressed=row["content_compressed"],
            token_count=row["token_count"] or 0,
            token_count_compressed=row["token_count_compressed"] or 0,
            file_path=row["file_path"],
            line_start=row["line_start"],
            line_end=row["line_end"],
            symbol_name=row["symbol_name"],
            signature=row["signature"],
            docstring=row["docstring"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            source=row["source"],
            confidence=row["confidence"] or 1.0,
            feature=row["feature"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            extra=json.loads(row["extra"]) if row["extra"] else {},
        )

    def _row_to_edge(self, row: sqlite3.Row) -> ChunkEdge:
        """Convert database row to ChunkEdge."""
        return ChunkEdge(
            source_id=row["source_id"],
            target_id=row["target_id"],
            edge_type=EdgeType(row["edge_type"]),
            weight=row["weight"] or 1.0,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def get_all_chunk_ids(self) -> List[str]:
        """Get all chunk IDs in the graph."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chunk_id FROM chunks")
            return [row[0] for row in cursor.fetchall()]

    def get_all_edges(self) -> List[ChunkEdge]:
        """Get all edges in the graph."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM edges")
            return [self._row_to_edge(row) for row in cursor.fetchall()]
