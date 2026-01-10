"""Tests for cfa.remember and cfa.recall tools."""
import tempfile
from pathlib import Path
import pytest

from src.cfa_v4.tools.memory import cfa_remember, cfa_recall, cfa_forget


@pytest.mark.asyncio
async def test_remember_creates_memory():
    """Test that remember creates a new memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize .claude directory
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        result = await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="test value",
            tags=["test", "example"]
        )

        assert result["success"] is True
        assert result["action"] == "created"
        assert result["key"] == "test-key"
        assert result["total_memories"] == 1


@pytest.mark.asyncio
async def test_remember_updates_existing():
    """Test that remember updates an existing memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        # Create first
        await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="original value",
            tags=["test"]
        )

        # Update
        result = await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="updated value",
            tags=["updated"]
        )

        assert result["success"] is True
        assert result["action"] == "updated"
        assert result["total_memories"] == 1


@pytest.mark.asyncio
async def test_remember_append():
    """Test that remember can append to existing value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        # Create
        await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="first line"
        )

        # Append
        result = await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="second line",
            append=True
        )

        # Verify appended
        recall_result = await cfa_recall(project_path=tmpdir, key="test-key")
        value = recall_result["results"][0]["value"]

        assert "first line" in value
        assert "second line" in value


@pytest.mark.asyncio
async def test_recall_by_key():
    """Test recall with exact key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        await cfa_remember(
            project_path=tmpdir,
            key="test-key",
            value="test value"
        )

        result = await cfa_recall(project_path=tmpdir, key="test-key")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["results"][0]["key"] == "test-key"
        assert result["results"][0]["value"] == "test value"


@pytest.mark.asyncio
async def test_recall_by_query():
    """Test recall with text query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        await cfa_remember(tmpdir, "auth-pattern", "JWT authentication")
        await cfa_remember(tmpdir, "api-pattern", "REST API design")

        result = await cfa_recall(project_path=tmpdir, query="auth")

        assert result["success"] is True
        assert result["count"] == 1
        assert result["results"][0]["key"] == "auth-pattern"


@pytest.mark.asyncio
async def test_recall_by_tags():
    """Test recall with tag filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        await cfa_remember(tmpdir, "mem1", "value1", tags=["pattern"])
        await cfa_remember(tmpdir, "mem2", "value2", tags=["gotcha"])
        await cfa_remember(tmpdir, "mem3", "value3", tags=["pattern", "gotcha"])

        result = await cfa_recall(project_path=tmpdir, tags=["pattern"])

        assert result["success"] is True
        assert result["count"] == 2

        keys = [r["key"] for r in result["results"]]
        assert "mem1" in keys
        assert "mem3" in keys


@pytest.mark.asyncio
async def test_recall_empty():
    """Test recall with no memories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        result = await cfa_recall(project_path=tmpdir)

        assert result["success"] is True
        assert result["count"] == 0
        assert "No memories" in result["message"]


@pytest.mark.asyncio
async def test_forget():
    """Test that forget deletes a memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        await cfa_remember(tmpdir, "test-key", "test value")

        result = await cfa_forget(project_path=tmpdir, key="test-key")

        assert result["success"] is True
        assert result["deleted_key"] == "test-key"
        assert result["remaining_memories"] == 0

        # Verify it's gone
        recall_result = await cfa_recall(tmpdir, key="test-key")
        assert recall_result["count"] == 0


@pytest.mark.asyncio
async def test_forget_nonexistent():
    """Test that forget fails on nonexistent key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir) / ".claude"
        claude_dir.mkdir()
        (claude_dir / "memories.json").write_text("[]")

        result = await cfa_forget(project_path=tmpdir, key="nonexistent")

        assert result["success"] is False
        assert "error" in result
