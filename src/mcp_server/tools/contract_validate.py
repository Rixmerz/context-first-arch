"""
MCP Tool: contract.validate

Validate implementation against contract.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.project import get_project_paths
from src.core.contract_parser import parse_contract, validate_contract_vs_impl


async def contract_validate(
    project_path: str,
    contract_file: str
) -> Dict[str, Any]:
    """
    Validate implementation against its contract.

    Checks if the implementation exports all functions defined
    in the contract, with matching signatures.

    Args:
        project_path: Path to CFA project
        contract_file: Relative path to contract (e.g., "contracts/user.contract.md")

    Returns:
        Dictionary with:
            - success: Boolean
            - valid: Whether implementation matches contract
            - issues: List of discrepancies
            - warnings: List of warnings

    Example:
        result = await contract_validate(
            project_path="/projects/my-app",
            contract_file="contracts/user.contract.md"
        )
    """
    try:
        path = Path(project_path)
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

        # Get project paths (handles both v1 and v2)
        paths = get_project_paths(path)
        impl_dir = paths["impl_dir"]

        # Find corresponding implementation
        impl_name = contract_path.stem.replace(".contract", "")

        # Try different extensions
        impl_path = None
        for ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".rs"]:
            candidate = impl_dir / f"{impl_name}{ext}"
            if candidate.exists():
                impl_path = candidate
                break

        if not impl_path:
            impl_prefix = impl_dir.relative_to(path)
            return {
                "success": False,
                "error": f"Implementation not found for contract: {impl_name}",
                "hint": f"Expected file at {impl_prefix}/{impl_name}.{{ts|py|rs}}"
            }

        # Analyze implementation
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(impl_path)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer for: {impl_path.suffix}"
            }

        analysis = analyzer.analyze_file(impl_path)

        # Validate
        result = validate_contract_vs_impl(contract, analysis)

        return {
            "success": True,
            "valid": result["valid"],
            "contract": contract_file,
            "implementation": str(impl_path.relative_to(path)),
            "issues": result["issues"],
            "warnings": result["warnings"],
            "summary": {
                "contract_functions": result["contract_functions"],
                "implemented_functions": result["impl_functions"],
                "missing": list(set(result["contract_functions"]) - set(result["impl_functions"])),
                "extra": list(set(result["impl_functions"]) - set(result["contract_functions"]))
            },
            "message": "Contract valid" if result["valid"] else f"Contract has {len(result['issues'])} issues"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Validation failed: {str(e)}"
        }
