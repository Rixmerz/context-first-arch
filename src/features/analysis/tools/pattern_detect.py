"""
MCP Tool: pattern.detect

Detect code patterns and consistency across the codebase.
"""

from typing import Any, Dict
from pathlib import Path

from src.features.analysis import get_registry
from src.core.project import get_project_paths
from src.features.analysis import detect_patterns


async def pattern_detect(
    project_path: str,
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Detect code patterns and identify inconsistencies.

    Analyzes the entire codebase for:
    - Naming conventions (camelCase, snake_case, PascalCase)
    - Import styles (named, default, wildcard)
    - Function length patterns

    Identifies files that deviate from project standards.

    Args:
        project_path: Path to CFA project
        threshold: Consistency threshold (0.0-1.0). Files below this are flagged.
                  Default: 0.8 (80% consistency required)

    Returns:
        Dictionary with:
            - success: Boolean
            - naming_patterns: Naming convention analysis
            - import_patterns: Import style analysis
            - function_patterns: Function length analysis
            - inconsistencies: List of files violating patterns
            - summary: Overall pattern statistics

    Example:
        result = await pattern_detect(
            project_path="/projects/my-app",
            threshold=0.75
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

        # Detect patterns
        result = detect_patterns(analyses, threshold=threshold)

        # Format response
        return {
            "success": True,
            "naming_patterns": {
                "dominant": result.naming_patterns["project_dominant"],
                "consistency": result.naming_patterns["consistency"],
                "distribution": result.naming_patterns["distribution"]
            },
            "import_patterns": {
                "dominant": result.import_patterns["project_dominant"],
                "consistency": result.import_patterns["consistency"],
                "distribution": result.import_patterns["distribution"]
            },
            "function_patterns": {
                "avg_length": round(result.function_patterns["project_avg"], 1),
                "max_length": result.function_patterns["project_max"],
                "min_length": result.function_patterns["project_min"],
                "distribution": result.function_patterns["distribution"]
            },
            "inconsistencies": _format_inconsistencies(result.inconsistencies),
            "summary": {
                "total_files_analyzed": len(analyses),
                "total_inconsistencies": len(result.inconsistencies),
                "naming_consistency": f"{result.naming_patterns['consistency'] * 100:.1f}%",
                "import_consistency": f"{result.import_patterns['consistency'] * 100:.1f}%"
            },
            "message": _format_summary_message(result, len(analyses))
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Pattern detection failed: {str(e)}"
        }


def _format_inconsistencies(inconsistencies: list) -> list:
    """Format inconsistencies for better readability."""
    formatted = []

    for inc in inconsistencies:
        entry = {
            "file": inc["file"],
            "type": inc["type"]
        }

        if inc["type"] in ["naming", "import_style"]:
            entry["expected"] = inc["expected"]
            entry["actual"] = inc["actual"]
            entry["consistency"] = f"{inc['consistency'] * 100:.1f}%"
        elif inc["type"] == "function_length":
            entry["issue"] = inc["issue"]
            entry["max_length"] = inc["max_length"]
            entry["project_avg"] = round(inc["project_avg"], 1)

        formatted.append(entry)

    return formatted


def _format_summary_message(result: Any, total_files: int) -> str:
    """Generate human-readable summary message."""
    naming_consistency = result.naming_patterns["consistency"]
    import_consistency = result.import_patterns["consistency"]
    inconsistency_count = len(result.inconsistencies)

    if inconsistency_count == 0:
        return f"✓ All {total_files} files follow consistent patterns"

    # Categorize inconsistencies
    naming_issues = sum(1 for i in result.inconsistencies if i["type"] == "naming")
    import_issues = sum(1 for i in result.inconsistencies if i["type"] == "import_style")
    length_issues = sum(1 for i in result.inconsistencies if i["type"] == "function_length")

    parts = []
    if naming_issues > 0:
        parts.append(f"{naming_issues} naming")
    if import_issues > 0:
        parts.append(f"{import_issues} import")
    if length_issues > 0:
        parts.append(f"{length_issues} length")

    dominant_naming = result.naming_patterns["project_dominant"]
    dominant_import = result.import_patterns["project_dominant"]

    return (
        f"Found {inconsistency_count} inconsistency/ies ({', '.join(parts)}). "
        f"Project standards: {dominant_naming} naming, {dominant_import} imports"
    )
