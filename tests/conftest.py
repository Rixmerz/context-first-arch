"""Pytest configuration and fixtures for CFA v4 tests."""
import pytest


@pytest.fixture
def sample_project_structure():
    """Fixture providing a sample project structure definition."""
    return {
        "name": "test-project",
        "files": [
            ".claude/map.md",
            ".claude/decisions.md",
            ".claude/current-task.md",
            ".claude/settings.json",
            ".claude/memories.json"
        ]
    }
