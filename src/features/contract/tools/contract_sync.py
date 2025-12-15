"""
MCP Tool: contract.sync

Sync contracts from code changes (code-first workflow).
"""

from typing import Any, Dict
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.project import get_project_paths
from src.features.contract import (
    parse_contract,
    generate_contract_from_analysis,
    render_contract
)


async def contract_sync(
    project_path: str,
    impl_file: str,
    auto_apply: bool = False
) -> Dict[str, Any]:
    """
    Sync contract from implementation code changes.

    Generates a new contract based on current implementation and compares
    with existing contract. Shows diff and optionally applies changes.

    This enables code-first workflow where implementation drives contracts.

    Args:
        project_path: Path to CFA project
        impl_file: Relative path to implementation (e.g., "impl/user.ts")
        auto_apply: If True, automatically update contract file

    Returns:
        Dictionary with:
            - success: Boolean
            - diff_preview: Formatted diff showing changes
            - changes: Added and removed functions
            - applied: Whether changes were applied
            - contract_file: Path to contract

    Example:
        # Preview changes
        result = await contract_sync(
            project_path="/projects/my-app",
            impl_file="impl/user.ts"
        )

        # Apply changes
        result = await contract_sync(
            project_path="/projects/my-app",
            impl_file="impl/user.ts",
            auto_apply=True
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

        # Normalize impl file path based on actual impl location
        impl_prefix = str(impl_dir.relative_to(path))
        target_path = impl_file
        if not target_path.startswith(impl_prefix):
            target_path = f"{impl_prefix}/{impl_file}"

        full_impl_path = path / target_path

        if not full_impl_path.exists():
            return {
                "success": False,
                "error": f"Implementation file not found: {target_path}"
            }

        # Analyze implementation
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(full_impl_path)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer available for: {full_impl_path.suffix}"
            }

        try:
            analysis = analyzer.analyze_file(full_impl_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze implementation: {str(e)}"
            }

        # Find or infer contract file
        feature_name = full_impl_path.stem
        contract_file = path / "contracts" / f"{feature_name}.contract.md"

        # Parse existing contract (if exists)
        old_contract = None
        if contract_file.exists():
            old_contract = parse_contract(str(contract_file))

        # Preserve purpose and other metadata from old contract
        purpose = old_contract.purpose if old_contract else f"(Generated from {target_path})"
        name = old_contract.name if old_contract else feature_name

        # Generate new contract from implementation
        new_contract = generate_contract_from_analysis(
            file_analysis=analysis,
            name=name,
            purpose=purpose
        )

        # Extract function lists for comparison
        old_funcs = _extract_function_names(old_contract.interface) if old_contract else []
        new_funcs = [f.name for f in analysis.functions if f.is_exported]

        # Compute diff
        added = set(new_funcs) - set(old_funcs)
        removed = set(old_funcs) - set(new_funcs)
        unchanged = set(new_funcs) & set(old_funcs)

        # Format diff
        diff_preview = _format_diff(added, removed, unchanged)

        # Determine if changes exist
        has_changes = len(added) > 0 or len(removed) > 0

        if not has_changes and not auto_apply:
            return {
                "success": True,
                "diff_preview": "No changes detected",
                "changes": {"added": [], "removed": []},
                "applied": False,
                "contract_file": str(contract_file.relative_to(path)),
                "message": "✓ Contract is already in sync with implementation"
            }

        # Apply changes if requested
        applied = False
        if auto_apply:
            # Ensure contracts directory exists
            contract_file.parent.mkdir(parents=True, exist_ok=True)

            # Render and save new contract
            contract_content = render_contract(new_contract)
            contract_file.write_text(contract_content)
            applied = True

        return {
            "success": True,
            "diff_preview": diff_preview,
            "changes": {
                "added": list(added),
                "removed": list(removed),
                "unchanged": list(unchanged)
            },
            "applied": applied,
            "contract_file": str(contract_file.relative_to(path)),
            "message": _format_message(added, removed, applied)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Contract sync failed: {str(e)}"
        }


def _extract_function_names(interface: str) -> list:
    """Extract function names from contract interface."""
    import re

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
                if func_name not in ['if', 'while', 'for', 'switch', 'catch']:
                    functions.append(func_name)
                break

    return list(set(functions))


def _format_diff(added: set, removed: set, unchanged: set) -> str:
    """Format diff preview."""
    lines = []

    if added:
        lines.append("**Added Functions**:")
        for func in sorted(added):
            lines.append(f"+ {func}()")
        lines.append("")

    if removed:
        lines.append("**Removed Functions**:")
        for func in sorted(removed):
            lines.append(f"- {func}()")
        lines.append("")

    if unchanged:
        lines.append(f"**Unchanged**: {len(unchanged)} function(s)")
        lines.append("")

    return "\n".join(lines) if lines else "No changes"


def _format_message(added: set, removed: set, applied: bool) -> str:
    """Generate human-readable message."""
    changes = []

    if added:
        changes.append(f"{len(added)} added")
    if removed:
        changes.append(f"{len(removed)} removed")

    if not changes:
        return "No changes detected"

    change_str = ", ".join(changes)

    if applied:
        return f"✓ Contract updated: {change_str}"
    else:
        return f"Preview: {change_str} (use auto_apply=True to apply)"
