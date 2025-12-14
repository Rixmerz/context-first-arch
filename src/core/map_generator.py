"""
Map generator for Context-First Architecture.

Generates and updates .claude/map.md with project analysis.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from src.core.analyzers import get_registry
from src.core.analyzers.base import FileAnalysis, FunctionInfo
from src.core.project import get_project_paths


@dataclass
class ProjectMap:
    """Represents the project map data."""
    description: str
    entry_points: List[str] = field(default_factory=list)
    data_flow: str = ""
    file_index: List[Dict[str, str]] = field(default_factory=list)
    current_state: List[str] = field(default_factory=list)
    non_obvious: List[str] = field(default_factory=list)


def generate_map(project_path: str) -> ProjectMap:
    """
    Generate project map from code analysis.

    Scans impl/, contracts/, shared/ and extracts:
    - Entry points
    - File purposes
    - Key functions
    - Data flow (inferred)

    Args:
        project_path: Path to CFA project

    Returns:
        ProjectMap with analysis results
    """
    path = Path(project_path)
    registry = get_registry()

    # Get project paths (handles both v1 and v2)
    paths = get_project_paths(path)

    # Collect all analyses
    analyses: List[FileAnalysis] = []

    # Scan impl/
    impl_dir = paths["impl_dir"]
    if impl_dir.exists():
        for file in impl_dir.rglob("*"):
            if file.is_file():
                analyzer = registry.get_analyzer_for_file(file)
                if analyzer:
                    analyses.append(analyzer.analyze_file(file))

    # Scan shared/
    shared_dir = paths["shared_dir"]
    if shared_dir.exists():
        for file in shared_dir.rglob("*"):
            if file.is_file():
                analyzer = registry.get_analyzer_for_file(file)
                if analyzer:
                    analyses.append(analyzer.analyze_file(file))

    # Build project map
    return _build_map(analyses, path)


def _build_map(analyses: List[FileAnalysis], project_path: Path) -> ProjectMap:
    """Build ProjectMap from file analyses."""

    # Collect entry points
    entry_points = []
    for analysis in analyses:
        rel_path = Path(analysis.path).relative_to(project_path)
        for ep in analysis.entry_points:
            entry_points.append(f"`{rel_path}:{ep}()`")

    # Build file index
    file_index = []
    for analysis in analyses:
        rel_path = Path(analysis.path).relative_to(project_path)

        # Determine purpose from file name and content
        purpose = _infer_purpose(analysis)

        # Get key functions (exported ones)
        key_funcs = [f.name for f in analysis.functions if f.is_exported][:5]

        file_index.append({
            "file": str(rel_path),
            "purpose": purpose,
            "key_functions": ", ".join(key_funcs) if key_funcs else "(none)"
        })

    # Infer data flow from call relationships
    data_flow = _infer_data_flow(analyses)

    # Current state (placeholder)
    current_state = ["- ⏳ Map generated from code analysis"]

    return ProjectMap(
        description="(analyze contracts/ for description)",
        entry_points=entry_points or ["- (no entry points detected)"],
        data_flow=data_flow or "[Input] → [Process] → [Output]",
        file_index=file_index,
        current_state=current_state,
        non_obvious=[]
    )


def _infer_purpose(analysis: FileAnalysis) -> str:
    """Infer file purpose from analysis."""
    filename = Path(analysis.path).stem.lower()

    # Common patterns
    if "type" in filename:
        return "Type definitions"
    elif "error" in filename:
        return "Error classes"
    elif "util" in filename:
        return "Utility functions"
    elif "api" in filename or "handler" in filename:
        return "API handlers"
    elif "db" in filename or "database" in filename:
        return "Database operations"
    elif "auth" in filename:
        return "Authentication"
    elif "user" in filename:
        return "User management"
    elif "test" in filename:
        return "Tests"

    # Infer from exports
    if analysis.types:
        return f"Defines: {', '.join(analysis.types[:3])}"
    elif analysis.exports:
        return f"Exports: {', '.join(analysis.exports[:3])}"

    return "(unknown purpose)"


def _infer_data_flow(analyses: List[FileAnalysis]) -> str:
    """Infer data flow from function calls."""
    # Build call graph
    call_graph: Dict[str, List[str]] = {}

    for analysis in analyses:
        for func in analysis.functions:
            if func.calls:
                call_graph[func.name] = func.calls

    # Find entry points and their call chains
    entry_funcs = []
    for analysis in analyses:
        entry_funcs.extend(analysis.entry_points)

    if not entry_funcs:
        return "[Input] → [Process] → [Output]"

    # Build simple flow from first entry point
    flow_parts = []
    visited = set()

    def trace_flow(func_name: str, depth: int = 0):
        if depth > 5 or func_name in visited:
            return
        visited.add(func_name)
        flow_parts.append(func_name)

        if func_name in call_graph:
            for called in call_graph[func_name][:2]:  # Limit branching
                trace_flow(called, depth + 1)

    for entry in entry_funcs[:1]:  # Just first entry point
        trace_flow(entry)

    if flow_parts:
        return " → ".join(flow_parts[:6])  # Limit length

    return "[Input] → [Process] → [Output]"


def render_map(project_map: ProjectMap) -> str:
    """Render ProjectMap to markdown."""

    # Entry points
    entry_points_md = "\n".join(
        f"- {ep}" if not ep.startswith("-") else ep
        for ep in project_map.entry_points
    )

    # File index table
    file_rows = []
    for entry in project_map.file_index:
        file_rows.append(
            f"| {entry['file']} | {entry['purpose']} | {entry['key_functions']} |"
        )
    file_index_md = "\n".join(file_rows) if file_rows else "| (no files analyzed) | | |"

    # Current state
    current_state_md = "\n".join(project_map.current_state)

    # Non-obvious things
    non_obvious_md = "\n".join(
        f"- {item}" for item in project_map.non_obvious
    ) if project_map.non_obvious else "(none documented yet)"

    return f"""# Project Map

## What This Project Does
{project_map.description}

## Entry Points
{entry_points_md}

## Data Flow
{project_map.data_flow}

## File Purpose Index
| File | Purpose | Key Functions |
|------|---------|---------------|
{file_index_md}

## Current State
{current_state_md}

## Non-Obvious Things
{non_obvious_md}
"""


def update_map_file(project_path: str) -> Dict[str, Any]:
    """
    Generate and save updated map.md.

    Returns dict with stats about the update.
    """
    project_map = generate_map(project_path)
    content = render_map(project_map)

    map_file = Path(project_path) / ".claude" / "map.md"
    map_file.write_text(content)

    return {
        "files_analyzed": len(project_map.file_index),
        "entry_points_found": len(project_map.entry_points),
        "updated_at": datetime.now().isoformat()
    }
