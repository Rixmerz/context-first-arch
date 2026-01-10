"""Tests for cfa.checkpoint tool."""
import tempfile
import subprocess
from pathlib import Path
import pytest

from src.cfa_v4.tools.checkpoint import cfa_checkpoint


def init_git_repo(path: str) -> None:
    """Initialize a git repository for testing."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=path,
        capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=path,
        capture_output=True
    )
    # Create initial commit
    test_file = Path(path) / "test.txt"
    test_file.write_text("initial content")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=path,
        capture_output=True
    )


@pytest.mark.asyncio
async def test_checkpoint_requires_git():
    """Test that checkpoint fails without git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await cfa_checkpoint(
            project_path=tmpdir,
            action="create",
            message="test checkpoint"
        )

        assert result["success"] is False
        assert "git" in result.get("error", "").lower()


@pytest.mark.asyncio
async def test_checkpoint_create():
    """Test creating a checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_git_repo(tmpdir)

        # Make a change
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("modified content")

        result = await cfa_checkpoint(
            project_path=tmpdir,
            action="create",
            message="Test checkpoint",
            include_untracked=True
        )

        assert result["success"] is True
        assert "checkpoint_id" in result
        assert result["message"] == "Test checkpoint"


@pytest.mark.asyncio
async def test_checkpoint_list():
    """Test listing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_git_repo(tmpdir)

        # Create a checkpoint
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("modified")
        await cfa_checkpoint(
            tmpdir, action="create", message="CP1", include_untracked=True
        )

        # List checkpoints
        result = await cfa_checkpoint(project_path=tmpdir, action="list")

        assert result["success"] is True
        assert "checkpoints" in result
        assert len(result["checkpoints"]) >= 1

        # Check checkpoint format
        cp = result["checkpoints"][0]
        assert "id" in cp
        assert "message" in cp
        assert cp["message"] == "CP1"


@pytest.mark.asyncio
async def test_checkpoint_rollback_dry_run():
    """Test rollback with dry_run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_git_repo(tmpdir)

        # Create checkpoint
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("checkpoint content")
        cp_result = await cfa_checkpoint(
            tmpdir, action="create", message="CP", include_untracked=True
        )

        checkpoint_id = cp_result["checkpoint_id"]

        # Make another change
        test_file.write_text("new content")

        # Dry run rollback
        result = await cfa_checkpoint(
            project_path=tmpdir,
            action="rollback",
            checkpoint_id=checkpoint_id,
            dry_run=True
        )

        assert result["success"] is True
        assert result["dry_run"] is True

        # Verify content wasn't actually rolled back
        assert test_file.read_text() == "new content"


@pytest.mark.asyncio
async def test_checkpoint_rollback():
    """Test actual rollback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        init_git_repo(tmpdir)

        # Create checkpoint
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("checkpoint content")
        cp_result = await cfa_checkpoint(
            tmpdir, action="create", message="CP", include_untracked=True
        )

        checkpoint_id = cp_result["checkpoint_id"]

        # Make another change and commit
        test_file.write_text("new content")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Another change"],
            cwd=tmpdir,
            capture_output=True
        )

        # Rollback
        result = await cfa_checkpoint(
            project_path=tmpdir,
            action="rollback",
            checkpoint_id=checkpoint_id,
            dry_run=False
        )

        assert result["success"] is True
        assert result["action"] == "rolled_back"
        assert result["checkpoint_id"] == checkpoint_id

        # Verify content was rolled back
        assert test_file.read_text() == "checkpoint content"
