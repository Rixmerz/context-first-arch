"""
Dependency graph analysis for Context-First Architecture.

Builds and analyzes dependency graphs from FileAnalysis data.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque


@dataclass
class FileNode:
    """Represents a file in the dependency graph."""
    path: str
    dependencies: List[str] = field(default_factory=list)  # files this imports
    dependents: List[str] = field(default_factory=list)    # files that import this
    feature: str = ""


@dataclass
class DependencyGraph:
    """Complete dependency graph for a project."""
    nodes: Dict[str, FileNode] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)


def build_dependency_graph(analyses: List[Any], project_path: Path) -> DependencyGraph:
    """
    Build a dependency graph from file analyses.

    Args:
        analyses: List of FileAnalysis objects
        project_path: Root path of the project

    Returns:
        DependencyGraph with nodes, edges, and detected cycles
    """
    graph = DependencyGraph()

    # Create nodes for all files
    for analysis in analyses:
        rel_path = str(Path(analysis.path).relative_to(project_path))
        feature = _infer_feature(rel_path)

        node = FileNode(
            path=rel_path,
            dependencies=[],
            dependents=[],
            feature=feature
        )
        graph.nodes[rel_path] = node

    # Build edges from imports
    for analysis in analyses:
        source_path = str(Path(analysis.path).relative_to(project_path))

        for imp in analysis.imports:
            # Resolve import to file path
            target_path = _resolve_import(imp.module, source_path, graph.nodes, project_path)

            if target_path and target_path in graph.nodes:
                # Add dependency edge
                if target_path not in graph.nodes[source_path].dependencies:
                    graph.nodes[source_path].dependencies.append(target_path)
                    graph.edges.append((source_path, target_path))

                # Add dependent edge (reverse)
                if source_path not in graph.nodes[target_path].dependents:
                    graph.nodes[target_path].dependents.append(source_path)

    # Detect cycles
    graph.cycles = detect_cycles(graph)

    return graph


def get_dependencies(graph: DependencyGraph, file_path: str, transitive: bool = False) -> List[str]:
    """
    Get dependencies for a file.

    Args:
        graph: Dependency graph
        file_path: Path to file
        transitive: If True, return all transitive dependencies (BFS)

    Returns:
        List of file paths that this file depends on
    """
    if file_path not in graph.nodes:
        return []

    if not transitive:
        return graph.nodes[file_path].dependencies

    # BFS for transitive dependencies
    visited = set()
    queue = deque([file_path])
    dependencies = []

    while queue:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        if current != file_path:  # Don't include self
            dependencies.append(current)

        # Add direct dependencies to queue
        for dep in graph.nodes[current].dependencies:
            if dep not in visited:
                queue.append(dep)

    return dependencies


def get_dependents(graph: DependencyGraph, file_path: str, transitive: bool = False) -> List[str]:
    """
    Get dependents for a file (files that depend on this file).

    Args:
        graph: Dependency graph
        file_path: Path to file
        transitive: If True, return all transitive dependents (BFS)

    Returns:
        List of file paths that depend on this file
    """
    if file_path not in graph.nodes:
        return []

    if not transitive:
        return graph.nodes[file_path].dependents

    # BFS for transitive dependents
    visited = set()
    queue = deque([file_path])
    dependents = []

    while queue:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        if current != file_path:  # Don't include self
            dependents.append(current)

        # Add direct dependents to queue
        for dep in graph.nodes[current].dependents:
            if dep not in visited:
                queue.append(dep)

    return dependents


def detect_cycles(graph: DependencyGraph) -> List[List[str]]:
    """
    Detect circular dependencies using DFS.

    Args:
        graph: Dependency graph

    Returns:
        List of cycles, where each cycle is a list of file paths
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> bool:
        """DFS with cycle detection."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.nodes[node].dependencies:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Found cycle - extract cycle from path
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.remove(node)
        return False

    # Run DFS from each unvisited node
    for node in graph.nodes:
        if node not in visited:
            dfs(node)

    return cycles


def get_feature_dependencies(
    graph: DependencyGraph,
    feature_name: str
) -> Dict[str, Any]:
    """
    Get all dependencies for a feature.

    Args:
        graph: Dependency graph
        feature_name: Feature name (e.g., "user", "auth")

    Returns:
        Dictionary with:
            - files: Files in this feature
            - dependencies: Features this depends on
            - dependents: Features that depend on this
            - external_deps: External dependencies
    """
    # Find all files in this feature
    feature_files = [
        path for path, node in graph.nodes.items()
        if node.feature == feature_name
    ]

    if not feature_files:
        return {
            "files": [],
            "dependencies": [],
            "dependents": [],
            "external_deps": []
        }

    # Collect all dependencies across feature files
    all_deps = set()
    for file_path in feature_files:
        deps = get_dependencies(graph, file_path, transitive=False)
        all_deps.update(deps)

    # Categorize dependencies
    feature_deps = defaultdict(list)
    external_deps = []

    for dep in all_deps:
        if dep in graph.nodes:
            dep_feature = graph.nodes[dep].feature
            if dep_feature and dep_feature != feature_name:
                feature_deps[dep_feature].append(dep)
        else:
            external_deps.append(dep)

    # Find dependents (features that depend on this one)
    all_dependents = set()
    for file_path in feature_files:
        dependents = get_dependents(graph, file_path, transitive=False)
        all_dependents.update(dependents)

    feature_dependents = defaultdict(list)
    for dependent in all_dependents:
        if dependent in graph.nodes:
            dep_feature = graph.nodes[dependent].feature
            if dep_feature and dep_feature != feature_name:
                feature_dependents[dep_feature].append(dependent)

    return {
        "files": feature_files,
        "dependencies": {feat: files for feat, files in feature_deps.items()},
        "dependents": {feat: files for feat, files in feature_dependents.items()},
        "external_deps": external_deps
    }


def _infer_feature(file_path: str) -> str:
    """
    Infer feature name from file path.

    For CFA projects:
    - impl/user.ts -> "user"
    - impl/auth/login.ts -> "auth"
    - shared/types.ts -> "shared"
    """
    parts = Path(file_path).parts

    if len(parts) < 2:
        return ""

    # CFA structure: impl/feature.ext or impl/feature/file.ext
    if parts[0] == "impl":
        if len(parts) == 2:
            # impl/user.ts -> "user"
            return Path(parts[1]).stem
        else:
            # impl/auth/login.ts -> "auth"
            return parts[1]
    elif parts[0] == "shared":
        return "shared"
    elif parts[0] == "contracts":
        return Path(parts[1]).stem.replace(".contract", "")

    return ""


def _resolve_import(
    module: str,
    source_path: str,
    nodes: Dict[str, FileNode],
    project_path: Path
) -> Optional[str]:
    """
    Resolve import statement to actual file path.

    Handles relative imports and CFA-style imports.
    """
    # Skip external modules (node_modules, standard library)
    if not module.startswith(".") and not module.startswith("/"):
        # Check if it's an internal module (CFA structure)
        for prefix in ["impl/", "shared/", "contracts/"]:
            # Try direct match
            for ext in [".ts", ".tsx", ".js", ".py", ".rs"]:
                candidate = f"{prefix}{module}{ext}"
                if candidate in nodes:
                    return candidate

                # Try with index
                candidate_index = f"{prefix}{module}/index{ext}"
                if candidate_index in nodes:
                    return candidate_index

        return None

    # Resolve relative import
    source_dir = str(Path(source_path).parent)
    resolved = str((Path(source_dir) / module).resolve())

    # Try to match with known nodes
    for node_path in nodes:
        node_resolved = str((project_path / node_path).resolve())
        # Check with and without extension
        if resolved == node_resolved or resolved.startswith(node_resolved):
            return node_path

    return None
