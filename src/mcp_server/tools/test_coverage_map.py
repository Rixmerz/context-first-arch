"""
MCP Tool: test.coverage_map

Map tests to contract requirements.
"""

from typing import Any, Dict
from pathlib import Path
import re

from src.core.contract_parser import parse_contract
from src.core.test_analyzer import analyze_test_coverage


async def test_coverage_map(
    project_path: str,
    contract_file: str
) -> Dict[str, Any]:
    """
    Map test coverage to contract requirements.

    Analyzes test files to determine which contract functions
    are covered by tests and which are missing test coverage.

    Args:
        project_path: Path to CFA project
        contract_file: Relative path to contract (e.g., "contracts/user.contract.md")

    Returns:
        Dictionary with:
            - success: Boolean
            - feature: Feature name
            - contract_functions: All functions in contract
            - tested_functions: Functions with test coverage
            - untested_functions: Functions missing tests
            - test_files: Test files found
            - coverage_percentage: Coverage percentage (0-100)
            - test_details: Details of each test and what it covers
            - summary: Coverage summary

    Example:
        result = await test_coverage_map(
            project_path="/projects/my-app",
            contract_file="contracts/user.contract.md"
        )
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {"success": False, "error": "Not a CFA project (missing .claude/)"}

        contract_path = path / contract_file

        if not contract_path.exists():
            return {
                "success": False,
                "error": f"Contract not found: {contract_file}"
            }

        # Parse contract
        contract = parse_contract(str(contract_path))

        if not contract:
            return {
                "success": False,
                "error": f"Failed to parse contract: {contract_file}"
            }

        # Extract function names from contract
        contract_functions = _extract_contract_functions(contract.interface)

        if not contract_functions:
            return {
                "success": False,
                "error": "No functions found in contract interface",
                "hint": "Contract may be empty or malformed"
            }

        # Get feature name from contract file
        feature_name = contract_path.stem.replace(".contract", "")

        # Analyze test coverage
        coverage = analyze_test_coverage(
            project_path=path,
            feature=feature_name,
            contract_functions=contract_functions
        )

        # Format response
        return {
            "success": True,
            "feature": feature_name,
            "contract": contract_file,
            "contract_functions": coverage.contract_functions,
            "tested_functions": coverage.tested_functions,
            "untested_functions": coverage.untested_functions,
            "test_files": coverage.test_files,
            "coverage_percentage": round(coverage.coverage_percentage, 1),
            "test_details": coverage.test_details,
            "summary": {
                "total_functions": len(coverage.contract_functions),
                "tested_count": len(coverage.tested_functions),
                "untested_count": len(coverage.untested_functions),
                "test_file_count": len(coverage.test_files),
                "coverage": f"{coverage.coverage_percentage:.1f}%"
            },
            "message": _format_message(coverage)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Test coverage analysis failed: {str(e)}"
        }


def _extract_contract_functions(interface: str) -> list:
    """
    Extract function names from contract interface.

    Supports various function declaration styles:
    - function name(...)
    - def name(...)
    - const name = (...)
    - export function name(...)
    """
    functions = []

    for line in interface.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Patterns for function declarations
        patterns = [
            r'(?:function|def|fn|const|export\s+function|export\s+const|async\s+function)\s+(\w+)\s*\(',
            r'(\w+)\s*[=:]\s*(?:async\s*)?\(',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                # Filter out common keywords
                if func_name not in ['if', 'while', 'for', 'switch', 'catch']:
                    functions.append(func_name)
                break

    return list(set(functions))  # Remove duplicates


def _format_message(coverage: Any) -> str:
    """Generate human-readable message."""
    if coverage.coverage_percentage == 0:
        if not coverage.test_files:
            return f"❌ No tests found for {coverage.feature}"
        else:
            return f"❌ Tests exist but don't cover contract functions ({len(coverage.test_files)} test file(s))"

    if coverage.coverage_percentage == 100:
        return f"✓ Full test coverage: all {len(coverage.contract_functions)} functions tested"

    tested = len(coverage.tested_functions)
    untested = len(coverage.untested_functions)

    return (
        f"{coverage.coverage_percentage:.1f}% coverage: "
        f"{tested} tested, {untested} untested"
    )
