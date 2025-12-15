"""
MCP Tool: impact.analyze

Calculate impact and risk of code changes.
"""

from typing import Any, Dict
from pathlib import Path

from src.features.analysis import get_registry
from src.core.project import get_project_paths
from src.features.analysis import build_dependency_graph
from src.features.analysis import analyze_impact


async def impact_analyze(
    project_path: str,
    file_path: str,
    change_type: str = "modify"
) -> Dict[str, Any]:
    """
    Analyze the impact of changing a file.

    Calculates blast radius, risk score, and provides recommendations
    for managing the change safely.

    Args:
        project_path: Path to CFA project
        file_path: Relative path to file (e.g., "impl/user.ts")
        change_type: Type of change - "add", "modify", or "delete"

    Returns:
        Dictionary with:
            - success: Boolean
            - file_path: File being analyzed
            - change_type: Type of change
            - affected_files: List of files that depend on this one
            - affected_count: Number of affected files
            - risk_score: Risk score (0.0-1.0)
            - risk_level: Risk level (low/medium/high/critical)
            - has_tests: Whether tests exist for this file
            - recommendations: List of recommendations
            - summary: Human-readable summary

    Example:
        # Analyze impact of modifying a file
        result = await impact_analyze(
            project_path="/projects/my-app",
            file_path="impl/auth.ts",
            change_type="modify"
        )

        # Analyze impact of deleting a file
        result = await impact_analyze(
            project_path="/projects/my-app",
            file_path="impl/deprecated.ts",
            change_type="delete"
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        # Validate change type
        valid_change_types = ["add", "modify", "delete"]
        if change_type not in valid_change_types:
            return {
                "success": False,
                "error": f"Invalid change_type: {change_type}",
                "hint": f"Must be one of: {', '.join(valid_change_types)}"
            }

        # Get project paths (handles both v1 and v2)
        paths = get_project_paths(path)
        impl_dir = paths["impl_dir"]

        if not impl_dir.exists():
            return {
                "success": False,
                "error": f"No impl directory found at {impl_dir.relative_to(path)}"
            }

        # Normalize file path based on actual impl location
        impl_prefix = str(impl_dir.relative_to(path))
        target_path = file_path
        if not target_path.startswith(impl_prefix):
            target_path = f"{impl_prefix}/{target_path}"

        # Analyze all files
        registry = get_registry()
        analyses = []

        for impl_file in impl_dir.rglob("*"):
            if impl_file.is_file():
                analyzer = registry.get_analyzer_for_file(impl_file)
                if analyzer:
                    try:
                        analysis = analyzer.analyze_file(impl_file)
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

        # Check if file exists in graph (for modify/delete)
        if change_type in ["modify", "delete"] and target_path not in graph.nodes:
            return {
                "success": False,
                "error": f"File not found in dependency graph: {target_path}",
                "hint": "Available files: " + ", ".join(list(graph.nodes.keys())[:5])
            }

        # Analyze impact
        impact = analyze_impact(
            graph=graph,
            file_path=target_path,
            change_type=change_type,
            project_path=path
        )

        # Format response
        return {
            "success": True,
            "file_path": impact.file_path,
            "change_type": impact.change_type,
            "affected_files": impact.affected_files,
            "affected_count": impact.affected_count,
            "risk_score": round(impact.risk_score, 2),
            "risk_level": impact.risk_level,
            "has_tests": impact.has_tests,
            "recommendations": impact.recommendations,
            "graph_stats": {
                "total_files": len(graph.nodes),
                "total_cycles": len(graph.cycles)
            },
            "summary": _format_summary(impact),
            "message": _format_message(impact)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Impact analysis failed: {str(e)}"
        }


def _format_summary(impact: Any) -> Dict[str, Any]:
    """Generate structured summary."""
    return {
        "blast_radius": f"{impact.affected_count} files",
        "risk_assessment": f"{impact.risk_level.upper()} ({impact.risk_score:.2f})",
        "test_coverage": "✓ Tests exist" if impact.has_tests else "❌ No tests",
        "change_type": impact.change_type,
        "recommendation_count": len(impact.recommendations)
    }


def _format_message(impact: Any) -> str:
    """Generate human-readable message."""
    risk_emoji = {
        "low": "✓",
        "medium": "⚠️",
        "high": "⚠️",
        "critical": "🚨"
    }

    emoji = risk_emoji.get(impact.risk_level, "")
    test_status = "with tests" if impact.has_tests else "without tests"

    return (
        f"{emoji} {impact.risk_level.upper()} risk: "
        f"{impact.change_type} affects {impact.affected_count} file(s) "
        f"({test_status})"
    )
