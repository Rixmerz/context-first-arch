"""
MCP Tool: contract.create

Create a contract from implementation code.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.contract_parser import generate_contract_from_analysis, render_contract


async def contract_create(
    project_path: str,
    impl_file: str,
    name: Optional[str] = None,
    purpose: str = ""
) -> Dict[str, Any]:
    """
    Create a contract.md from implementation code.

    Analyzes the implementation file and generates a contract
    with the public interface, inferred dependencies, etc.

    Args:
        project_path: Path to CFA project
        impl_file: Relative path to implementation file (e.g., "impl/user.ts")
        name: Optional contract name (defaults to filename)
        purpose: Optional purpose description

    Returns:
        Dictionary with:
            - success: Boolean
            - contract_path: Path to created contract
            - preview: First 500 chars of contract

    Example:
        result = await contract_create(
            project_path="/projects/my-app",
            impl_file="impl/user.ts",
            name="User",
            purpose="User management: CRUD operations and authentication"
        )
    """
    try:
        path = Path(project_path)
        contracts_dir = path / "contracts"
        impl_path = path / impl_file

        if not contracts_dir.exists():
            return {
                "success": False,
                "error": f"Not a CFA project: {project_path} (missing contracts/)"
            }

        if not impl_path.exists():
            return {
                "success": False,
                "error": f"Implementation file not found: {impl_file}"
            }

        # Analyze implementation
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(impl_path)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer for file type: {impl_path.suffix}"
            }

        analysis = analyzer.analyze_file(impl_path)

        if analysis.errors:
            return {
                "success": False,
                "error": f"Analysis errors: {', '.join(analysis.errors)}"
            }

        # Generate contract
        contract_name = name or impl_path.stem.replace("_", " ").title()
        contract = generate_contract_from_analysis(
            analysis,
            name=contract_name,
            purpose=purpose
        )

        # Render and save
        content = render_contract(contract)
        contract_filename = f"{impl_path.stem}.contract.md"
        contract_path = contracts_dir / contract_filename
        contract_path.write_text(content)

        return {
            "success": True,
            "contract_path": str(contract_path.relative_to(path)),
            "name": contract_name,
            "functions_documented": len([f for f in analysis.functions if f.is_exported]),
            "preview": content[:600] + "..." if len(content) > 600 else content,
            "next_steps": [
                "1. Review and edit the contract",
                "2. Add error definitions",
                "3. Document side effects",
                "4. Add usage examples"
            ],
            "message": f"Contract created: {contract_filename}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create contract: {str(e)}"
        }
