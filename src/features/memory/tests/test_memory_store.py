"""
Tests for Memory Store

Tests the core MemoryStore functionality including:
- CRUD operations (set, get, delete)
- Search by query and tags
- Edit/append operations
- Statistics
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.features.memory import MemoryStore, Memory


class TestMemoryStore:
    """Tests for MemoryStore class."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with .claude folder."""
        temp_dir = tempfile.mkdtemp()
        claude_dir = Path(temp_dir) / ".claude"
        claude_dir.mkdir()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def store(self, temp_project):
        """Create a MemoryStore instance for testing."""
        return MemoryStore(temp_project)

    def test_set_and_get(self, store):
        """Test setting and getting a memory."""
        # Set a memory
        memory = store.set(
            key="test-key",
            value="test-value",
            tags=["tag1", "tag2"]
        )

        assert memory.key == "test-key"
        assert memory.value == "test-value"
        assert memory.tags == ["tag1", "tag2"]

        # Get the memory
        retrieved = store.get("test-key")
        assert retrieved is not None
        assert retrieved.key == "test-key"
        assert retrieved.value == "test-value"

    def test_get_nonexistent(self, store):
        """Test getting a memory that doesn't exist."""
        result = store.get("nonexistent")
        assert result is None

    def test_delete(self, store):
        """Test deleting a memory."""
        store.set(key="to-delete", value="some value")

        # Delete
        deleted = store.delete("to-delete")
        assert deleted is True

        # Verify gone
        assert store.get("to-delete") is None

    def test_delete_nonexistent(self, store):
        """Test deleting a memory that doesn't exist."""
        deleted = store.delete("nonexistent")
        assert deleted is False

    def test_search_by_query(self, store):
        """Test searching memories by query string."""
        store.set(key="mem1", value="hello world")
        store.set(key="mem2", value="hello universe")
        store.set(key="mem3", value="goodbye world")

        results = store.search(query="hello")
        assert len(results) == 2
        keys = [m.key for m in results]
        assert "mem1" in keys
        assert "mem2" in keys

    def test_search_by_tags(self, store):
        """Test searching memories by tags."""
        store.set(key="mem1", value="val1", tags=["arch", "security"])
        store.set(key="mem2", value="val2", tags=["arch"])
        store.set(key="mem3", value="val3", tags=["testing"])

        # Single tag
        results = store.search(tags=["arch"])
        assert len(results) == 2

        # Multiple tags (AND logic)
        results = store.search(tags=["arch", "security"])
        assert len(results) == 1
        assert results[0].key == "mem1"

    def test_edit_replace(self, store):
        """Test editing a memory (replace mode)."""
        store.set(key="edit-me", value="original")

        updated = store.edit(key="edit-me", new_value="updated")
        assert updated is not None
        assert updated.value == "updated"

        # Verify persisted
        retrieved = store.get("edit-me")
        assert retrieved.value == "updated"

    def test_edit_append(self, store):
        """Test editing a memory (append mode)."""
        store.set(key="append-me", value="line1")

        updated = store.edit(key="append-me", new_value="line2", append=True)
        assert updated is not None
        assert "line1" in updated.value
        assert "line2" in updated.value

    def test_list_all(self, store):
        """Test listing all memories."""
        store.set(key="a", value="val1")
        store.set(key="b", value="val2")
        store.set(key="c", value="val3")

        all_memories = store.list_all()
        assert len(all_memories) == 3

    def test_list_all_with_limit(self, store):
        """Test listing memories with limit."""
        for i in range(10):
            store.set(key=f"mem{i}", value=f"val{i}")

        limited = store.list_all(limit=5)
        assert len(limited) == 5

    def test_stats(self, store):
        """Test getting memory store statistics."""
        store.set(key="m1", value="v1", tags=["a", "b"])
        store.set(key="m2", value="v2", tags=["a"])
        store.set(key="m3", value="v3", tags=["c"])

        stats = store.get_stats()
        assert stats["total_memories"] == 3
        assert stats["unique_tags"] == 3
        assert "a" in stats["tag_counts"]
        assert stats["tag_counts"]["a"] == 2


class TestMemoryDataclass:
    """Tests for Memory dataclass."""

    def test_memory_creation(self):
        """Test creating a Memory instance."""
        memory = Memory(
            key="test",
            value="test value",
            timestamp="2024-01-01T00:00:00",
            tags=["tag1"],
            project_path="/test/path"
        )

        assert memory.key == "test"
        assert memory.value == "test value"
        assert memory.tags == ["tag1"]
