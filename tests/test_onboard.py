"""Tests for cfa.onboard tool."""
import tempfile
import shutil
from pathlib import Path
import pytest

from src.cfa_v4.tools.onboard import cfa_onboard


@pytest.mark.asyncio
async def test_onboard_init_creates_structure():
    """Test that onboard with init_if_missing creates .claude/ structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await cfa_onboard(
            project_path=tmpdir,
            init_if_missing=True
        )

        assert result["success"] is True
        assert result["initialized"] is True
        assert result["project_name"] == Path(tmpdir).name

        # Check files were created
        claude_dir = Path(tmpdir) / ".claude"
        assert claude_dir.exists()
        assert (claude_dir / "map.md").exists()
        assert (claude_dir / "decisions.md").exists()
        assert (claude_dir / "current-task.md").exists()
        assert (claude_dir / "settings.json").exists()
        assert (claude_dir / "memories.json").exists()


@pytest.mark.asyncio
async def test_onboard_without_init_fails():
    """Test that onboard fails without init_if_missing when not initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await cfa_onboard(
            project_path=tmpdir,
            init_if_missing=False
        )

        assert result["success"] is False
        assert result["initialized"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_onboard_loads_context():
    """Test that onboard loads context from existing .claude/ directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize first
        await cfa_onboard(project_path=tmpdir, init_if_missing=True)

        # Write some content
        claude_dir = Path(tmpdir) / ".claude"
        (claude_dir / "map.md").write_text("# My Project\n\nTest content")

        # Load context
        result = await cfa_onboard(project_path=tmpdir)

        assert result["success"] is True
        assert "Test content" in result["context"]
        assert result["files_loaded"]["map"] is True


@pytest.mark.asyncio
async def test_onboard_includes_memories_summary():
    """Test that onboard includes memories summary when requested."""
    with tempfile.TemporaryDirectory() as tmpdir:
        await cfa_onboard(project_path=tmpdir, init_if_missing=True)

        # Add a memory
        import json
        claude_dir = Path(tmpdir) / ".claude"
        memories = [
            {
                "key": "test-memory",
                "value": "test value",
                "tags": ["test"],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]
        (claude_dir / "memories.json").write_text(json.dumps(memories))

        # Load with memories
        result = await cfa_onboard(
            project_path=tmpdir,
            include_memories_summary=True
        )

        assert result["success"] is True
        assert "test-memory" in result["context"]
        assert "1 total" in result["context"]


@pytest.mark.asyncio
async def test_onboard_truncates_large_context():
    """Test that onboard truncates context when it exceeds max_context_chars."""
    with tempfile.TemporaryDirectory() as tmpdir:
        await cfa_onboard(project_path=tmpdir, init_if_missing=True)

        # Write large content
        large_content = "X" * 10000
        claude_dir = Path(tmpdir) / ".claude"
        (claude_dir / "map.md").write_text(large_content)

        # Load with small limit
        result = await cfa_onboard(
            project_path=tmpdir,
            max_context_chars=500
        )

        assert result["success"] is True
        assert result["truncated"] is True
        assert len(result["context"]) <= 600  # Some overhead for truncation message
