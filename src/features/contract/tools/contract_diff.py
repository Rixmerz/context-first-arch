"""
MCP Tool: contract.diff

Compare contract against implementation with detailed diff.
"""

from typing import Any, Dict, List
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.project import get_project_paths
from src.features.contract import parse_contract


async def contract_diff(
    project_path: str,
    contract_file: str,
    impl_file: str = ""
) -> Dict[str, Any]:
    """
    Compare contract against implementation with detailed signature analysis.

    Provides enhanced diff showing:
    - Implemented functions (signature matches)
    - Missing functions (in contract, not in impl)
    - Extra functions (in impl, not in contract)
    - Signature changes (name matches but signature differs)

    Args:
        project_path: Path to CFA project
        contract_file: Relative path to contract (e.g., "contracts/user.contract.md")
        impl_file: Optional explicit implementation file path

    Returns:
        Dictionary with:
            - success: Boolean
            - implemented: Functions correctly implemented
            - missing: Functions not yet implemented
            - extra: Functions not in contract
            - signature_changes: Functions with signature mismatches
            - summary: Overall statistics

    Example:
        result = await contract_diff(
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

        # Get project paths (handles both v1 and v2)
        paths = get_project_paths(path)
        impl_dir = paths["impl_dir"]

        # Find implementation file
        if impl_file:
            impl_path = path / impl_file
        else:
            impl_name = contract_path.stem.replace(".contract", "")
            impl_path = None

            for ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".rs"]:
                candidate = impl_dir / f"{impl_name}{ext}"
                if candidate.exists():
                    impl_path = candidate
                    break

        if not impl_path or not impl_path.exists():
            impl_prefix = impl_dir.relative_to(path)
            return {
                "success": False,
                "error": f"Implementation not found",
                "hint": f"Expected file at {impl_prefix}/{contract_path.stem.replace('.contract', '')}.{{ts|py|rs}}"
            }

        # Analyze implementation
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(impl_path)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer available for: {impl_path.suffix}"
            }

        analysis = analyzer.analyze_file(impl_path)

        # Compare contract vs implementation
        diff_result = _compute_diff(contract, analysis)

        return {
            "success": True,
            "contract": contract_file,
            "implementation": str(impl_path.relative_to(path)),
            "implemented": diff_result["implemented"],
            "missing": diff_result["missing"],
            "extra": diff_result["extra"],
            "signature_changes": diff_result["signature_changes"],
            "summary": {
                "total_contract_functions": len(diff_result["contract_functions"]),
                "total_impl_functions": len(diff_result["impl_functions"]),
                "implemented_count": len(diff_result["implemented"]),
                "missing_count": len(diff_result["missing"]),
                "extra_count": len(diff_result["extra"]),
                "signature_changes_count": len(diff_result["signature_changes"])
            },
            "message": _format_summary_message(diff_result)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Diff failed: {str(e)}"
        }


def _compute_diff(contract: Any, analysis: Any) -> Dict[str, Any]:
    """
    Compute detailed diff between contract and implementation.

    Returns dict with implemented, missing, extra, and signature_changes lists.
    """
    import re

    # Extract functions from contract interface
    contract_funcs = {}
    for line in contract.interface.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Extract function name and signature
        # Patterns: function name(...), def name(...), const name = (...), export function name(...)
        patterns = [
            r'(?:function|def|fn|const|export\s+function|export\s+const|async\s+function)\s+(\w+)\s*(\([^)]*\))',
            r'(\w+)\s*[=:]\s*(?:async\s*)?\(([^)]*)\)',
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1)
                params = match.group(2) if '(' in match.group(2) else f"({match.group(2)})"
                contract_funcs[name] = {"name": name, "signature": line.strip(), "params": params}
                break

    # Get implemented functions
    impl_funcs = {}
    for func in analysis.functions:
        if func.is_exported:
            impl_funcs[func.name] = {
                "name": func.name,
                "signature": func.signature,
                "params": f"({', '.join(p.get('name', '') for p in func.parameters)})"
            }

    contract_names = set(contract_funcs.keys())
    impl_names = set(impl_funcs.keys())

    # Categorize functions
    implemented = []
    missing = []
    extra = []
    signature_changes = []

    # Check contract functions
    for name in contract_names:
        if name in impl_names:
            # Function exists - check if signature matches
            contract_sig = contract_funcs[name]
            impl_sig = impl_funcs[name]

            # Normalize signatures for comparison
            if _signatures_match(contract_sig["params"], impl_sig["params"]):
                implemented.append({
                    "name": name,
                    "signature": impl_sig["signature"]
                })
            else:
                signature_changes.append({
                    "name": name,
                    "contract_signature": contract_sig["signature"],
                    "impl_signature": impl_sig["signature"]
                })
        else:
            missing.append({
                "name": name,
                "signature": contract_funcs[name]["signature"]
            })

    # Check for extra implementations
    for name in impl_names - contract_names:
        extra.append({
            "name": name,
            "signature": impl_funcs[name]["signature"]
        })

    return {
        "contract_functions": list(contract_names),
        "impl_functions": list(impl_names),
        "implemented": implemented,
        "missing": missing,
        "extra": extra,
        "signature_changes": signature_changes
    }


def _signatures_match(contract_params: str, impl_params: str) -> bool:
    """
    Compare parameter signatures (simple heuristic).

    Normalizes whitespace and checks parameter count.
    """
    # Remove whitespace and extract param names
    contract_normalized = contract_params.replace(" ", "").strip("()")
    impl_normalized = impl_params.replace(" ", "").strip("()")

    # If both empty, match
    if not contract_normalized and not impl_normalized:
        return True

    # Count parameters (split by comma, filter empty)
    contract_param_count = len([p for p in contract_normalized.split(",") if p])
    impl_param_count = len([p for p in impl_normalized.split(",") if p])

    # Match if param count is same (basic check)
    return contract_param_count == impl_param_count


def _format_summary_message(diff_result: Dict[str, Any]) -> str:
    """Generate human-readable summary message."""
    total = len(diff_result["contract_functions"])
    implemented = len(diff_result["implemented"])
    missing = len(diff_result["missing"])
    extra = len(diff_result["extra"])
    sig_changes = len(diff_result["signature_changes"])

    if missing == 0 and sig_changes == 0:
        return f"✓ All {total} contract functions implemented correctly"

    parts = []
    if implemented > 0:
        parts.append(f"{implemented} implemented")
    if missing > 0:
        parts.append(f"{missing} missing")
    if sig_changes > 0:
        parts.append(f"{sig_changes} signature mismatch")
    if extra > 0:
        parts.append(f"{extra} extra")

    return ", ".join(parts)
