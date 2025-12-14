"""
Test coverage analysis for Context-First Architecture.

Maps tests to contract requirements and implementation files.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Optional

from src.core.project import get_project_paths


@dataclass
class TestCoverage:
    """Test coverage analysis results."""
    feature: str
    contract_functions: List[str]
    tested_functions: List[str]
    untested_functions: List[str]
    test_files: List[str]
    coverage_percentage: float
    test_details: List[Dict[str, Any]] = field(default_factory=list)


def analyze_test_coverage(
    project_path: Path,
    feature: str,
    contract_functions: List[str]
) -> TestCoverage:
    """
    Analyze test coverage for a feature against its contract.

    Args:
        project_path: Root path of the project
        feature: Feature name (e.g., "user", "auth")
        contract_functions: List of function names from contract

    Returns:
        TestCoverage with mapping of tests to contract functions
    """
    # Find test files for this feature
    test_files = find_test_files(project_path, feature)

    if not test_files:
        # No tests found
        return TestCoverage(
            feature=feature,
            contract_functions=contract_functions,
            tested_functions=[],
            untested_functions=contract_functions,
            test_files=[],
            coverage_percentage=0.0
        )

    # Extract test cases from test files
    tested_functions = set()
    test_details = []

    for test_file in test_files:
        test_cases = extract_test_cases(test_file)

        for test_case in test_cases:
            # Match test case to contract functions
            matched_functions = match_test_to_functions(
                test_case["name"],
                contract_functions
            )

            if matched_functions:
                tested_functions.update(matched_functions)
                test_details.append({
                    "test_name": test_case["name"],
                    "test_file": str(test_file.relative_to(project_path)),
                    "line": test_case["line"],
                    "covers": matched_functions
                })

    # Calculate coverage
    untested = [f for f in contract_functions if f not in tested_functions]
    coverage = (len(tested_functions) / len(contract_functions) * 100) if contract_functions else 0

    return TestCoverage(
        feature=feature,
        contract_functions=contract_functions,
        tested_functions=list(tested_functions),
        untested_functions=untested,
        test_files=[str(f.relative_to(project_path)) for f in test_files],
        coverage_percentage=coverage,
        test_details=test_details
    )


def find_test_files(project_path: Path, feature: str) -> List[Path]:
    """
    Find test files for a feature.

    Searches common test patterns:
    - tests/{feature}.test.{ext}
    - tests/{feature}_test.{ext}
    - __tests__/{feature}.spec.{ext}
    - {feature}.test.{ext}
    """
    test_files = []

    # Get project paths (handles both v1 and v2)
    paths = get_project_paths(project_path)
    impl_dir = paths["impl_dir"]

    # Common test directory patterns
    test_dirs = [
        project_path / "tests",
        project_path / "__tests__",
        project_path / "test",
        project_path / "spec",
        impl_dir / "__tests__"
    ]

    # Common test file patterns
    patterns = [
        f"{feature}.test.*",
        f"{feature}_test.*",
        f"test_{feature}.*",
        f"{feature}.spec.*",
        f"{feature}_spec.*"
    ]

    # Search in test directories
    for test_dir in test_dirs:
        if test_dir.exists():
            for pattern in patterns:
                test_files.extend(test_dir.glob(pattern))

    # Also search in impl directory (co-located tests)
    if impl_dir.exists():
        for pattern in patterns:
            test_files.extend(impl_dir.glob(pattern))

    return list(set(test_files))  # Remove duplicates


def extract_test_cases(test_file: Path) -> List[Dict[str, Any]]:
    """
    Extract test case names from a test file.

    Supports common test frameworks:
    - Jest/Vitest: test('...'), it('...')
    - Pytest: def test_...()
    - Rust: #[test] fn test_...()
    """
    test_cases = []

    try:
        content = test_file.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines, start=1):
            # JavaScript/TypeScript patterns
            js_patterns = [
                r'(?:test|it)\s*\(\s*[\'"`](.+?)[\'"`]',  # test('name')
                r'(?:test|it)\s*\(\s*[\'"`](.+?)[\'"`]',  # it('name')
                r'describe\s*\(\s*[\'"`](.+?)[\'"`]',     # describe('name')
            ]

            for pattern in js_patterns:
                match = re.search(pattern, line)
                if match:
                    test_cases.append({
                        "name": match.group(1),
                        "line": i,
                        "type": "js"
                    })

            # Python patterns
            py_pattern = r'def\s+(test_\w+)\s*\('
            match = re.search(py_pattern, line)
            if match:
                test_cases.append({
                    "name": match.group(1),
                    "line": i,
                    "type": "python"
                })

            # Rust patterns
            if "#[test]" in line or "#[tokio::test]" in line:
                # Look for function on next line
                if i < len(lines):
                    next_line = lines[i]
                    rust_pattern = r'fn\s+(\w+)\s*\('
                    match = re.search(rust_pattern, next_line)
                    if match:
                        test_cases.append({
                            "name": match.group(1),
                            "line": i + 1,
                            "type": "rust"
                        })

    except Exception:
        # If file can't be read, return empty list
        pass

    return test_cases


def match_test_to_functions(
    test_name: str,
    contract_functions: List[str]
) -> List[str]:
    """
    Match a test name to contract functions.

    Uses heuristics to match test names to function names:
    - Direct match: test_getUserData -> getUserData
    - Partial match: should get user data -> getUserData
    - Camel/snake case conversion
    """
    matched = []

    # Normalize test name (remove test prefix, convert to lowercase)
    normalized_test = test_name.lower()
    normalized_test = re.sub(r'^test[_\s]', '', normalized_test)
    normalized_test = re.sub(r'[^\w]', '', normalized_test)

    for func in contract_functions:
        # Normalize function name
        normalized_func = re.sub(r'[^\w]', '', func.lower())

        # Check for matches
        if normalized_func in normalized_test or normalized_test in normalized_func:
            matched.append(func)
        elif _fuzzy_match(normalized_test, normalized_func):
            matched.append(func)

    return matched


def _fuzzy_match(test_name: str, func_name: str, threshold: float = 0.6) -> bool:
    """
    Fuzzy matching for test name to function name.

    Uses simple substring matching with threshold.
    """
    # Extract words from both names
    test_words = set(re.findall(r'\w+', test_name.lower()))
    func_words = set(re.findall(r'\w+', func_name.lower()))

    # Remove common words
    common_words = {"should", "test", "it", "when", "can", "will", "get", "set"}
    test_words = test_words - common_words
    func_words = func_words - common_words

    if not func_words:
        return False

    # Calculate overlap
    overlap = len(test_words & func_words)
    similarity = overlap / len(func_words)

    return similarity >= threshold
