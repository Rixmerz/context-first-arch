"""
MCP Tool: dependency.analyze

Analyze dependencies and dependents for features or files.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.project import get_project_paths
from src.core.dependency_analyzer import (
    build_dependency_graph,
    get_dependencies,
    get_dependents,
    get_feature_dependencies
)


async def dependency_analyze(
    project_path: str,
    target: str,
    target_type: str = "feature",
    transitive: bool = False
) -> Dict[str, Any]:
    """
    Analyze dependencies for a feature or file.

    Builds a complete dependency graph of the project and returns
    dependency information for the specified target.

    Args:
        project_path: Path to CFA project
        target: Feature name (e.g., "user") or file path (e.g., "impl/user.ts")
        target_type: Either "feature" or "file"
        transitive: If True, include transitive dependencies

    Returns:
        Dictionary with:
            - success: Boolean
            - dependencies: List of dependencies
            - dependents: List of dependents
            - cycles: Any circular dependencies detected
            - graph_stats: Overall graph statistics

    Example:
        # Analyze feature dependencies
        result = await dependency_analyze(
            project_path="/projects/my-app",
            target="user",
            target_type="feature"
        )

        # Analyze file dependencies
        result = await dependency_analyze(
            project_path="/projects/my-app",
            target="impl/auth.ts",
            target_type="file",
            transitive=True
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Get project paths (handles both v1 and v2)
        paths = get_project_paths(path)
        impl_dir = paths["impl_dir"]

        if not impl_dir.exists():
            return {
                "success": False,
                "error": f"No impl directory found at {impl_dir.relative_to(path)}"
            }

        # Analyze all files
        registry = get_registry()
        analyses = []

        for file_path in impl_dir.rglob("*"):
            if file_path.is_file():
                analyzer = registry.get_analyzer_for_file(file_path)
                if analyzer:
                    try:
                        analysis = analyzer.analyze_file(file_path)
                        analyses.append(analysis)
                    except Exception:
                        # Skip files that fail to analyze
                        continue

        if not analyses:
            return {
                "success": False,
                "error": "No analyzable files found in impl/"
            }

        # Build dependency graph
        graph = build_dependency_graph(analyses, path)

        # Analyze based on target type
        if target_type == "feature":
            result = get_feature_dependencies(graph, target)

            return {
                "success": True,
                "target": target,
                "target_type": "feature",
                "files": result["files"],
                "dependencies": result["dependencies"],
                "dependents": result["dependents"],
                "external_deps": result["external_deps"],
                "cycles": _find_cycles_for_feature(graph, target),
                "graph_stats": {
                    "total_files": len(graph.nodes),
                    "total_edges": len(graph.edges),
                    "total_cycles": len(graph.cycles)
                },
                "message": _format_feature_summary(result, target)
            }

        elif target_type == "file":
            # Normalize file path
            target_path = target
            if not target_path.startswith("impl/"):
                target_path = f"impl/{target_path}"

            if target_path not in graph.nodes:
                return {
                    "success": False,
                    "error": f"File not found in dependency graph: {target_path}",
                    "hint": "Available files: " + ", ".join(list(graph.nodes.keys())[:5])
                }

            dependencies = get_dependencies(graph, target_path, transitive=transitive)
            dependents = get_dependents(graph, target_path, transitive=transitive)

            # Check if file is part of any cycle
            file_cycles = [cycle for cycle in graph.cycles if target_path in cycle]

            return {
                "success": True,
                "target": target_path,
                "target_type": "file",
                "dependencies": dependencies,
                "dependents": dependents,
                "dependency_count": len(dependencies),
                "dependent_count": len(dependents),
                "in_cycle": len(file_cycles) > 0,
                "cycles": file_cycles,
                "graph_stats": {
                    "total_files": len(graph.nodes),
                    "total_edges": len(graph.edges),
                    "total_cycles": len(graph.cycles)
                },
                "message": _format_file_summary(dependencies, dependents, file_cycles)
            }

        else:
            return {
                "success": False,
                "error": f"Invalid target_type: {target_type} (must be 'feature' or 'file')"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Dependency analysis failed: {str(e)}"
        }


def _find_cycles_for_feature(graph: Any, feature_name: str) -> list:
    """Find all cycles involving files in the given feature."""
    feature_files = {
        path for path, node in graph.nodes.items()
        if node.feature == feature_name
    }

    # Filter cycles that involve any file from this feature
    feature_cycles = []
    for cycle in graph.cycles:
        if any(file_path in feature_files for file_path in cycle):
            feature_cycles.append(cycle)

    return feature_cycles


def _format_feature_summary(result: Dict[str, Any], feature_name: str) -> str:
    """Generate human-readable summary for feature analysis."""
    file_count = len(result["files"])
    dep_count = len(result["dependencies"])
    dependent_count = len(result["dependents"])
    external_count = len(result["external_deps"])

    if file_count == 0:
        return f"Feature '{feature_name}' not found in project"

    parts = [f"{file_count} file(s)"]

    if dep_count > 0:
        parts.append(f"depends on {dep_count} feature(s)")
    if dependent_count > 0:
        parts.append(f"used by {dependent_count} feature(s)")
    if external_count > 0:
        parts.append(f"{external_count} external dep(s)")

    return f"Feature '{feature_name}': " + ", ".join(parts)


def _format_file_summary(dependencies: list, dependents: list, cycles: list) -> str:
    """Generate human-readable summary for file analysis."""
    parts = []

    if dependencies:
        parts.append(f"{len(dependencies)} dependency/ies")
    if dependents:
        parts.append(f"{len(dependents)} dependent(s)")
    if cycles:
        parts.append(f"⚠️ {len(cycles)} circular dependency/ies")

    if not parts:
        return "No dependencies or dependents"

    return ", ".join(parts)
