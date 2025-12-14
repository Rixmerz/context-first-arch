"""
Pattern detection for Context-First Architecture.

Analyzes code patterns and consistency across the codebase.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List
from collections import Counter


@dataclass
class PatternAnalysis:
    """Results of pattern analysis."""
    naming_patterns: Dict[str, Any]
    import_patterns: Dict[str, Any]
    function_patterns: Dict[str, Any]
    inconsistencies: List[Dict[str, Any]]


def detect_patterns(analyses: List[Any], threshold: float = 0.8) -> PatternAnalysis:
    """
    Detect code patterns across file analyses.

    Analyzes:
    - Naming conventions (camelCase, snake_case, PascalCase)
    - Import styles (named vs default imports)
    - Function length patterns

    Args:
        analyses: List of FileAnalysis objects
        threshold: Consistency threshold (0.0-1.0). Files below this are flagged.

    Returns:
        PatternAnalysis with detected patterns and inconsistencies
    """
    naming = _analyze_naming(analyses)
    imports = _analyze_imports(analyses)
    functions = _analyze_functions(analyses)

    # Find inconsistencies
    inconsistencies = _find_inconsistencies(
        analyses, naming, imports, functions, threshold
    )

    return PatternAnalysis(
        naming_patterns=naming,
        import_patterns=imports,
        function_patterns=functions,
        inconsistencies=inconsistencies
    )


def _analyze_naming(analyses: List[Any]) -> Dict[str, Any]:
    """
    Analyze naming conventions.

    Detects:
    - camelCase (e.g., getUserData)
    - snake_case (e.g., get_user_data)
    - PascalCase (e.g., GetUserData)
    - kebab-case (e.g., get-user-data)
    """
    file_patterns = {}

    for analysis in analyses:
        patterns = {
            "camelCase": 0,
            "snake_case": 0,
            "PascalCase": 0,
            "kebab-case": 0
        }

        # Analyze function names
        for func in analysis.functions:
            name = func.name

            if re.match(r'^[a-z][a-zA-Z0-9]*$', name):
                patterns["camelCase"] += 1
            elif re.match(r'^[a-z][a-z0-9_]*$', name):
                patterns["snake_case"] += 1
            elif re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                patterns["PascalCase"] += 1
            elif re.match(r'^[a-z][a-z0-9-]*$', name):
                patterns["kebab-case"] += 1

        # Calculate dominant pattern for this file
        total = sum(patterns.values())
        if total > 0:
            dominant = max(patterns.items(), key=lambda x: x[1])
            file_patterns[analysis.path] = {
                "patterns": patterns,
                "dominant": dominant[0],
                "consistency": dominant[1] / total if total > 0 else 0
            }

    # Calculate overall project patterns
    all_patterns = Counter()
    for file_data in file_patterns.values():
        all_patterns[file_data["dominant"]] += 1

    project_total = sum(all_patterns.values())
    project_dominant = max(all_patterns.items(), key=lambda x: x[1])[0] if all_patterns else "unknown"

    return {
        "project_dominant": project_dominant,
        "distribution": dict(all_patterns),
        "consistency": all_patterns[project_dominant] / project_total if project_total > 0 else 0,
        "file_patterns": file_patterns
    }


def _analyze_imports(analyses: List[Any]) -> Dict[str, Any]:
    """
    Analyze import styles.

    Detects:
    - Named imports (import { foo } from 'bar')
    - Default imports (import foo from 'bar')
    - Wildcard imports (import * as foo from 'bar')
    """
    file_patterns = {}

    for analysis in analyses:
        patterns = {
            "named": 0,
            "default": 0,
            "wildcard": 0,
            "namespace": 0
        }

        for imp in analysis.imports:
            if imp.is_default:
                patterns["default"] += 1
            elif imp.names:
                if "*" in imp.names:
                    patterns["wildcard"] += 1
                elif imp.alias:
                    patterns["namespace"] += 1
                else:
                    patterns["named"] += 1

        # Calculate dominant pattern for this file
        total = sum(patterns.values())
        if total > 0:
            dominant = max(patterns.items(), key=lambda x: x[1])
            file_patterns[analysis.path] = {
                "patterns": patterns,
                "dominant": dominant[0],
                "consistency": dominant[1] / total if total > 0 else 0
            }

    # Calculate overall project patterns
    all_patterns = Counter()
    for file_data in file_patterns.values():
        all_patterns[file_data["dominant"]] += 1

    project_total = sum(all_patterns.values())
    project_dominant = max(all_patterns.items(), key=lambda x: x[1])[0] if all_patterns else "unknown"

    return {
        "project_dominant": project_dominant,
        "distribution": dict(all_patterns),
        "consistency": all_patterns[project_dominant] / project_total if project_total > 0 else 0,
        "file_patterns": file_patterns
    }


def _analyze_functions(analyses: List[Any]) -> Dict[str, Any]:
    """
    Analyze function patterns.

    Detects:
    - Function length distribution
    - Average function length
    - Outliers (very long or very short functions)
    """
    all_lengths = []
    file_patterns = {}

    for analysis in analyses:
        lengths = []
        for func in analysis.functions:
            length = func.end_line - func.start_line + 1
            lengths.append(length)
            all_lengths.append(length)

        if lengths:
            avg_length = sum(lengths) / len(lengths)
            max_length = max(lengths)
            min_length = min(lengths)

            file_patterns[analysis.path] = {
                "count": len(lengths),
                "avg_length": avg_length,
                "max_length": max_length,
                "min_length": min_length
            }

    # Calculate project-wide statistics
    if all_lengths:
        project_avg = sum(all_lengths) / len(all_lengths)
        project_max = max(all_lengths)
        project_min = min(all_lengths)

        # Define length categories
        short = sum(1 for l in all_lengths if l < 10)
        medium = sum(1 for l in all_lengths if 10 <= l < 50)
        long = sum(1 for l in all_lengths if 50 <= l < 100)
        very_long = sum(1 for l in all_lengths if l >= 100)

        return {
            "project_avg": project_avg,
            "project_max": project_max,
            "project_min": project_min,
            "distribution": {
                "short (<10 lines)": short,
                "medium (10-49 lines)": medium,
                "long (50-99 lines)": long,
                "very_long (100+ lines)": very_long
            },
            "file_patterns": file_patterns
        }

    return {
        "project_avg": 0,
        "project_max": 0,
        "project_min": 0,
        "distribution": {},
        "file_patterns": {}
    }


def _find_inconsistencies(
    analyses: List[Any],
    naming: Dict[str, Any],
    imports: Dict[str, Any],
    functions: Dict[str, Any],
    threshold: float
) -> List[Dict[str, Any]]:
    """
    Find files that violate project patterns.

    A file is inconsistent if its pattern usage is below threshold.
    """
    inconsistencies = []

    # Check naming inconsistencies
    project_naming = naming["project_dominant"]
    for analysis in analyses:
        file_path = analysis.path
        if file_path in naming["file_patterns"]:
            file_data = naming["file_patterns"][file_path]
            if file_data["dominant"] != project_naming:
                inconsistencies.append({
                    "file": file_path,
                    "type": "naming",
                    "expected": project_naming,
                    "actual": file_data["dominant"],
                    "consistency": file_data["consistency"]
                })

    # Check import inconsistencies
    project_imports = imports["project_dominant"]
    for analysis in analyses:
        file_path = analysis.path
        if file_path in imports["file_patterns"]:
            file_data = imports["file_patterns"][file_path]
            if file_data["dominant"] != project_imports:
                inconsistencies.append({
                    "file": file_path,
                    "type": "import_style",
                    "expected": project_imports,
                    "actual": file_data["dominant"],
                    "consistency": file_data["consistency"]
                })

    # Check function length outliers
    if functions["project_avg"] > 0:
        for analysis in analyses:
            file_path = analysis.path
            if file_path in functions["file_patterns"]:
                file_data = functions["file_patterns"][file_path]

                # Flag files with very long functions (3x average)
                if file_data["max_length"] > functions["project_avg"] * 3:
                    inconsistencies.append({
                        "file": file_path,
                        "type": "function_length",
                        "issue": "contains very long function",
                        "max_length": file_data["max_length"],
                        "project_avg": functions["project_avg"]
                    })

    return inconsistencies
