"""
Impact analysis for Context-First Architecture.

Calculates blast radius and risk scores for code changes.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.dependency_analyzer import DependencyGraph, get_dependents


@dataclass
class ImpactAnalysis:
    """Results of impact analysis."""
    file_path: str
    change_type: str
    affected_files: List[str]
    affected_count: int
    risk_score: float
    risk_level: str
    has_tests: bool
    recommendations: List[str]


def analyze_impact(
    graph: DependencyGraph,
    file_path: str,
    change_type: str = "modify",
    project_path: Optional[Path] = None
) -> ImpactAnalysis:
    """
    Analyze the impact of changing a file.

    Args:
        graph: Dependency graph
        file_path: File being changed
        change_type: Type of change ("add", "modify", "delete")
        project_path: Optional project path for test detection

    Returns:
        ImpactAnalysis with risk assessment and recommendations
    """
    # Get all transitive dependents
    affected_files = get_dependents(graph, file_path, transitive=True)
    affected_count = len(affected_files)
    total_files = len(graph.nodes)

    # Check for test coverage
    has_tests = _has_test_coverage(file_path, project_path) if project_path else False

    # Calculate risk score
    risk_score = _calculate_risk_score(
        affected_count=affected_count,
        total_files=total_files,
        change_type=change_type,
        has_tests=has_tests,
        in_cycle=_is_in_cycle(graph, file_path)
    )

    # Determine risk level
    risk_level = _determine_risk_level(risk_score)

    # Generate recommendations
    recommendations = _generate_recommendations(
        risk_level=risk_level,
        affected_count=affected_count,
        has_tests=has_tests,
        change_type=change_type,
        in_cycle=_is_in_cycle(graph, file_path)
    )

    return ImpactAnalysis(
        file_path=file_path,
        change_type=change_type,
        affected_files=affected_files,
        affected_count=affected_count,
        risk_score=risk_score,
        risk_level=risk_level,
        has_tests=has_tests,
        recommendations=recommendations
    )


def _calculate_risk_score(
    affected_count: int,
    total_files: int,
    change_type: str,
    has_tests: bool,
    in_cycle: bool
) -> float:
    """
    Calculate risk score (0.0 - 1.0).

    Formula: (affected_ratio * change_multiplier * test_factor * cycle_factor)
    """
    # Base: affected files ratio
    affected_ratio = affected_count / total_files if total_files > 0 else 0

    # Change type multiplier
    change_multipliers = {
        "add": 0.3,      # New code is lower risk
        "modify": 1.0,   # Modifications are baseline risk
        "delete": 1.5    # Deletions are higher risk (breaking changes)
    }
    change_multiplier = change_multipliers.get(change_type, 1.0)

    # Test coverage factor
    test_factor = 0.7 if has_tests else 1.3  # Tests reduce risk, no tests increase risk

    # Cycle factor
    cycle_factor = 1.5 if in_cycle else 1.0  # Circular dependencies increase risk

    # Calculate final score (clamped to 0-1)
    score = affected_ratio * change_multiplier * test_factor * cycle_factor
    return min(max(score, 0.0), 1.0)


def _determine_risk_level(risk_score: float) -> str:
    """Determine risk level from score."""
    if risk_score < 0.2:
        return "low"
    elif risk_score < 0.5:
        return "medium"
    elif risk_score < 0.8:
        return "high"
    else:
        return "critical"


def _generate_recommendations(
    risk_level: str,
    affected_count: int,
    has_tests: bool,
    change_type: str,
    in_cycle: bool
) -> List[str]:
    """Generate actionable recommendations based on risk analysis."""
    recommendations = []

    # Risk-based recommendations
    if risk_level == "critical":
        recommendations.append("⚠️ CRITICAL: Review all affected files before proceeding")
        recommendations.append("Consider breaking change into smaller incremental updates")
    elif risk_level == "high":
        recommendations.append("⚠️ HIGH RISK: Thorough testing required")
        recommendations.append("Review affected files for potential breaking changes")
    elif risk_level == "medium":
        recommendations.append("Medium risk: Test affected components")

    # Affected files recommendations
    if affected_count > 10:
        recommendations.append(f"Wide impact: {affected_count} files affected - consider regression testing")
    elif affected_count > 5:
        recommendations.append(f"Moderate impact: Review {affected_count} affected files")

    # Test coverage recommendations
    if not has_tests:
        recommendations.append("❌ No tests found - add tests before making changes")
    else:
        recommendations.append("✓ Tests exist - ensure they cover new changes")

    # Cycle recommendations
    if in_cycle:
        recommendations.append("⚠️ File is in circular dependency - refactor before major changes")

    # Change type recommendations
    if change_type == "delete":
        recommendations.append("Deletion: Verify no runtime dependencies exist")
    elif change_type == "modify":
        recommendations.append("Modification: Check for API contract changes")

    return recommendations


def _is_in_cycle(graph: DependencyGraph, file_path: str) -> bool:
    """Check if file is part of a circular dependency."""
    for cycle in graph.cycles:
        if file_path in cycle:
            return True
    return False


def _has_test_coverage(file_path: str, project_path: Path) -> bool:
    """
    Check if file has corresponding test coverage.

    Looks for common test patterns:
    - tests/{feature}.test.{ext}
    - tests/{feature}_test.{ext}
    - __tests__/{feature}.spec.{ext}
    - {feature}.test.{ext}
    """
    path = Path(file_path)
    feature_name = path.stem

    # Common test patterns
    test_patterns = [
        f"tests/{feature_name}.test.*",
        f"tests/{feature_name}_test.*",
        f"tests/test_{feature_name}.*",
        f"__tests__/{feature_name}.spec.*",
        f"__tests__/{feature_name}.test.*",
        f"{feature_name}.test.*",
        f"test_{feature_name}.*"
    ]

    # Check if any test file exists
    for pattern in test_patterns:
        matches = list(project_path.glob(pattern))
        if matches:
            return True

    return False
