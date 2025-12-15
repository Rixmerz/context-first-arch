"""
Coupling analysis for Context-First Architecture.

Analyzes feature coupling and identifies tight dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from src.core.dependency_analyzer import DependencyGraph


@dataclass
class CouplingScore:
    """Coupling score between two features."""
    feature_a: str
    feature_b: str
    imports_a_to_b: int
    imports_b_to_a: int
    coupling_score: float
    coupling_level: str


@dataclass
class CouplingAnalysis:
    """Complete coupling analysis results."""
    feature_pairs: List[CouplingScore] = field(default_factory=list)
    high_coupling: List[CouplingScore] = field(default_factory=list)
    low_coupling: List[CouplingScore] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)


def analyze_coupling(
    graph: DependencyGraph,
    high_threshold: float = 0.3,
    low_threshold: float = 0.1
) -> CouplingAnalysis:
    """
    Analyze coupling between features.

    Calculates coupling score for each feature pair based on
    cross-imports normalized by feature sizes.

    Formula:
        coupling_score = (imports_A→B + imports_B→A) / (|A| * |B|)

    Args:
        graph: Dependency graph
        high_threshold: Threshold for high coupling (default: 0.3)
        low_threshold: Threshold for low coupling (default: 0.1)

    Returns:
        CouplingAnalysis with scored feature pairs
    """
    # Group files by feature
    features = _group_by_feature(graph)

    if len(features) < 2:
        # Need at least 2 features to analyze coupling
        return CouplingAnalysis()

    # Calculate coupling for all feature pairs
    feature_pairs = []
    feature_names = list(features.keys())

    for i, feature_a in enumerate(feature_names):
        for feature_b in feature_names[i + 1:]:  # Only check each pair once
            if feature_a == feature_b:
                continue

            score = _calculate_coupling_score(
                graph=graph,
                feature_a=feature_a,
                feature_b=feature_b,
                files_a=features[feature_a],
                files_b=features[feature_b]
            )

            feature_pairs.append(score)

    # Categorize by coupling level
    high_coupling = [s for s in feature_pairs if s.coupling_score >= high_threshold]
    low_coupling = [s for s in feature_pairs if s.coupling_score < low_threshold]

    # Identify violations (high coupling that may need refactoring)
    violations = _identify_violations(high_coupling)

    # Sort by coupling score (highest first)
    feature_pairs.sort(key=lambda x: x.coupling_score, reverse=True)
    high_coupling.sort(key=lambda x: x.coupling_score, reverse=True)

    return CouplingAnalysis(
        feature_pairs=feature_pairs,
        high_coupling=high_coupling,
        low_coupling=low_coupling,
        violations=violations
    )


def _group_by_feature(graph: DependencyGraph) -> Dict[str, List[str]]:
    """Group files by feature."""
    features = defaultdict(list)

    for path, node in graph.nodes.items():
        if node.feature and node.feature != "shared":
            features[node.feature].append(path)

    return dict(features)


def _calculate_coupling_score(
    graph: DependencyGraph,
    feature_a: str,
    feature_b: str,
    files_a: List[str],
    files_b: List[str]
) -> CouplingScore:
    """
    Calculate coupling score between two features.

    Counts cross-imports and normalizes by feature sizes.
    """
    imports_a_to_b = 0
    imports_b_to_a = 0

    # Count imports from A to B
    for file_a in files_a:
        if file_a in graph.nodes:
            for dep in graph.nodes[file_a].dependencies:
                if dep in files_b:
                    imports_a_to_b += 1

    # Count imports from B to A
    for file_b in files_b:
        if file_b in graph.nodes:
            for dep in graph.nodes[file_b].dependencies:
                if dep in files_a:
                    imports_b_to_a += 1

    # Calculate normalized coupling score
    total_imports = imports_a_to_b + imports_b_to_a
    max_possible = len(files_a) * len(files_b)

    coupling_score = total_imports / max_possible if max_possible > 0 else 0

    # Determine coupling level
    coupling_level = _determine_coupling_level(coupling_score)

    return CouplingScore(
        feature_a=feature_a,
        feature_b=feature_b,
        imports_a_to_b=imports_a_to_b,
        imports_b_to_a=imports_b_to_a,
        coupling_score=coupling_score,
        coupling_level=coupling_level
    )


def _determine_coupling_level(score: float) -> str:
    """Determine coupling level from score."""
    if score >= 0.5:
        return "very_high"
    elif score >= 0.3:
        return "high"
    elif score >= 0.1:
        return "medium"
    else:
        return "low"


def _identify_violations(high_coupling: List[CouplingScore]) -> List[Dict[str, Any]]:
    """
    Identify coupling violations that may need refactoring.

    A violation is:
    - Very high coupling (>= 0.5) - features are too tightly coupled
    - Bidirectional high coupling - circular feature dependencies
    """
    violations = []

    for score in high_coupling:
        violation = {
            "features": f"{score.feature_a} ↔ {score.feature_b}",
            "score": score.coupling_score,
            "type": "",
            "recommendation": ""
        }

        # Very high coupling
        if score.coupling_score >= 0.5:
            violation["type"] = "very_high_coupling"
            violation["recommendation"] = (
                "Consider merging features or extracting shared abstractions"
            )
            violations.append(violation)

        # Bidirectional coupling
        elif score.imports_a_to_b > 0 and score.imports_b_to_a > 0:
            violation["type"] = "bidirectional_coupling"
            violation["recommendation"] = (
                "Refactor to unidirectional dependency or introduce interface layer"
            )
            violations.append(violation)

        # High coupling (single direction is OK for some cases)
        else:
            violation["type"] = "high_coupling"
            violation["recommendation"] = (
                "Review if this coupling is necessary or can be reduced"
            )
            violations.append(violation)

    return violations
