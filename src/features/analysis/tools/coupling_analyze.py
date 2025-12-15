"""
MCP Tool: coupling.analyze

Analyze feature coupling and dependencies.
"""

from typing import Any, Dict
from pathlib import Path

from src.features.analysis import get_registry
from src.core.project import get_project_paths
from src.features.analysis import build_dependency_graph
from src.features.analysis import analyze_coupling


async def coupling_analyze(
    project_path: str,
    high_threshold: float = 0.3,
    low_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Analyze coupling between features.

    Calculates coupling scores for all feature pairs based on
    cross-imports, identifies tightly coupled features, and
    suggests refactoring opportunities.

    Args:
        project_path: Path to CFA project
        high_threshold: Threshold for high coupling (0.0-1.0, default: 0.3)
        low_threshold: Threshold for low coupling (0.0-1.0, default: 0.1)

    Returns:
        Dictionary with:
            - success: Boolean
            - feature_pairs: All feature pair coupling scores
            - high_coupling: Pairs with high coupling
            - low_coupling: Pairs with low coupling
            - violations: Coupling violations needing attention
            - summary: Overall coupling statistics

    Example:
        result = await coupling_analyze(
            project_path="/projects/my-app",
            high_threshold=0.3,
            low_threshold=0.1
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Validate thresholds
        if not (0.0 <= low_threshold <= high_threshold <= 1.0):
            return {
                "success": False,
                "error": "Invalid thresholds",
                "hint": "Must satisfy: 0.0 <= low_threshold <= high_threshold <= 1.0"
            }

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

        # Analyze coupling
        coupling = analyze_coupling(
            graph=graph,
            high_threshold=high_threshold,
            low_threshold=low_threshold
        )

        if not coupling.feature_pairs:
            return {
                "success": True,
                "feature_pairs": [],
                "high_coupling": [],
                "low_coupling": [],
                "violations": [],
                "summary": {
                    "total_features": 0,
                    "total_pairs": 0
                },
                "message": "Not enough features to analyze coupling (need at least 2)"
            }

        # Format response
        return {
            "success": True,
            "feature_pairs": _format_coupling_scores(coupling.feature_pairs),
            "high_coupling": _format_coupling_scores(coupling.high_coupling),
            "low_coupling": _format_coupling_scores(coupling.low_coupling),
            "violations": coupling.violations,
            "summary": {
                "total_pairs": len(coupling.feature_pairs),
                "high_coupling_count": len(coupling.high_coupling),
                "low_coupling_count": len(coupling.low_coupling),
                "violation_count": len(coupling.violations),
                "thresholds": {
                    "high": high_threshold,
                    "low": low_threshold
                }
            },
            "message": _format_message(coupling)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Coupling analysis failed: {str(e)}"
        }


def _format_coupling_scores(scores: list) -> list:
    """Format coupling scores for output."""
    return [
        {
            "features": f"{s.feature_a} ↔ {s.feature_b}",
            "feature_a": s.feature_a,
            "feature_b": s.feature_b,
            "imports_a_to_b": s.imports_a_to_b,
            "imports_b_to_a": s.imports_b_to_a,
            "coupling_score": round(s.coupling_score, 3),
            "coupling_level": s.coupling_level
        }
        for s in scores
    ]


def _format_message(coupling: Any) -> str:
    """Generate human-readable message."""
    total = len(coupling.feature_pairs)
    high = len(coupling.high_coupling)
    violations = len(coupling.violations)

    if violations > 0:
        return (
            f"⚠️ {violations} coupling violation(s) found "
            f"({high} high coupling pairs out of {total} total)"
        )

    if high > 0:
        return (
            f"Found {high} high coupling pair(s) out of {total} total "
            f"(no critical violations)"
        )

    return f"✓ Good coupling: {total} feature pairs analyzed, all within acceptable ranges"
