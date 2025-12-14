"""
Onboarding workflow for CFA projects.

Generates initial context and validates project readiness
for AI-assisted development sessions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from src.core.project import get_project_paths


def generate_onboarding(
    project_path: str,
    include_contracts: bool = True,
    include_decisions: bool = True,
    max_context_size: int = 50000
) -> Dict[str, Any]:
    """
    Generate onboarding context for a project.

    Collects essential project information to provide
    comprehensive context for AI-assisted development.

    Args:
        project_path: Path to the project root
        include_contracts: Include contract summaries
        include_decisions: Include decision records
        max_context_size: Maximum context size in characters

    Returns:
        Dictionary with onboarding context
    """
    paths = get_project_paths(project_path)
    root = paths["root"]
    context_parts = []
    files_read = []

    # 1. Read map.md (project overview)
    map_file = paths["claude_dir"] / "map.md"
    if map_file.exists():
        map_content = map_file.read_text(encoding="utf-8")
        context_parts.append(f"# Project Map\n\n{map_content}")
        files_read.append(".claude/map.md")

    # 2. Read settings.json
    settings_file = paths["claude_dir"] / "settings.json"
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            context_parts.append(f"# Project Settings\n\n```json\n{json.dumps(settings, indent=2)}\n```")
            files_read.append(".claude/settings.json")
        except json.JSONDecodeError:
            pass

    # 3. Read current-task.md
    task_file = paths["claude_dir"] / "current-task.md"
    if task_file.exists():
        task_content = task_file.read_text(encoding="utf-8")
        context_parts.append(f"# Current Task\n\n{task_content}")
        files_read.append(".claude/current-task.md")

    # 4. Read decisions.md
    if include_decisions:
        decisions_file = paths["claude_dir"] / "decisions.md"
        if decisions_file.exists():
            decisions_content = decisions_file.read_text(encoding="utf-8")
            context_parts.append(f"# Architecture Decisions\n\n{decisions_content}")
            files_read.append(".claude/decisions.md")

    # 5. Summarize contracts
    if include_contracts:
        contracts_dir = paths["contracts_dir"]
        if contracts_dir.exists():
            contract_summaries = []
            for contract_file in contracts_dir.glob("*.contract.md"):
                try:
                    content = contract_file.read_text(encoding="utf-8")
                    # Extract first 500 chars or until first ##
                    summary = content[:500]
                    if "##" in summary:
                        summary = summary[:summary.index("##")]
                    contract_summaries.append(f"- **{contract_file.name}**: {summary.strip()[:200]}...")
                    files_read.append(f"contracts/{contract_file.name}")
                except Exception:
                    continue

            if contract_summaries:
                context_parts.append(f"# Contracts Overview\n\n" + "\n".join(contract_summaries))

    # 6. Detect project structure
    structure_info = _detect_project_structure(root, paths)
    context_parts.append(f"# Project Structure\n\n{structure_info}")

    # Combine context
    full_context = "\n\n---\n\n".join(context_parts)

    # Truncate if needed
    truncated = False
    if len(full_context) > max_context_size:
        full_context = full_context[:max_context_size] + "\n\n... (truncated)"
        truncated = True

    # Record onboarding
    _record_onboarding(paths["claude_dir"], files_read)

    return {
        "success": True,
        "project_path": str(root),
        "project_name": settings.get("name", root.name),
        "cfa_version": settings.get("cfa_version", "unknown"),
        "context": full_context,
        "context_size": len(full_context),
        "files_read": files_read,
        "truncated": truncated,
        "onboarding_recorded": True
    }


def check_onboarding_status(project_path: str) -> Dict[str, Any]:
    """
    Check if onboarding has been performed for current session.

    Returns information about the last onboarding and
    whether context refresh is recommended.

    Args:
        project_path: Path to the project root

    Returns:
        Dictionary with onboarding status
    """
    paths = get_project_paths(project_path)
    onboarding_file = paths["claude_dir"] / ".onboarding_status"

    if not onboarding_file.exists():
        return {
            "success": True,
            "onboarded": False,
            "recommendation": "Run workflow.onboard to load project context",
            "last_onboarding": None
        }

    try:
        status = json.loads(onboarding_file.read_text())
        last_time = datetime.fromisoformat(status.get("timestamp", ""))
        hours_ago = (datetime.now() - last_time).total_seconds() / 3600

        # Check if any key files have changed since onboarding
        files_changed = []
        for file_path in status.get("files_read", []):
            full_path = paths["root"] / file_path
            if full_path.exists():
                mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                if mtime > last_time:
                    files_changed.append(file_path)

        needs_refresh = hours_ago > 24 or len(files_changed) > 0

        return {
            "success": True,
            "onboarded": True,
            "last_onboarding": status.get("timestamp"),
            "hours_ago": round(hours_ago, 1),
            "files_read": status.get("files_read", []),
            "files_changed_since": files_changed,
            "needs_refresh": needs_refresh,
            "recommendation": (
                "Context may be stale - consider re-running workflow.onboard"
                if needs_refresh
                else "Onboarding is up to date"
            )
        }

    except (json.JSONDecodeError, ValueError):
        return {
            "success": True,
            "onboarded": False,
            "recommendation": "Onboarding status corrupted - run workflow.onboard",
            "last_onboarding": None
        }


def _detect_project_structure(root: Path, paths: Dict[str, Path]) -> str:
    """Detect and describe project structure."""
    structure_lines = []

    # Check for common project files
    indicators = {
        "package.json": "Node.js/JavaScript project",
        "pyproject.toml": "Python project",
        "Cargo.toml": "Rust project",
        "go.mod": "Go project",
        "pom.xml": "Java/Maven project",
        "build.gradle": "Java/Gradle project",
    }

    for file, description in indicators.items():
        if (root / file).exists():
            structure_lines.append(f"- **Type**: {description}")
            break

    # Check source directory
    impl_dir = paths.get("impl_dir")
    if impl_dir and impl_dir.exists():
        file_count = sum(1 for _ in impl_dir.rglob("*") if _.is_file())
        structure_lines.append(f"- **Implementation**: {impl_dir.relative_to(root)} ({file_count} files)")

    shared_dir = paths.get("shared_dir")
    if shared_dir and shared_dir.exists():
        structure_lines.append(f"- **Shared code**: {shared_dir.relative_to(root)}")

    # Check for tests
    for test_dir in ["tests", "test", "__tests__"]:
        if (root / test_dir).exists():
            structure_lines.append(f"- **Tests**: {test_dir}/")
            break

    return "\n".join(structure_lines) if structure_lines else "- Structure not detected"


def _record_onboarding(claude_dir: Path, files_read: List[str]):
    """Record onboarding status to file."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "files_read": files_read
    }

    onboarding_file = claude_dir / ".onboarding_status"
    onboarding_file.write_text(json.dumps(status, indent=2))
