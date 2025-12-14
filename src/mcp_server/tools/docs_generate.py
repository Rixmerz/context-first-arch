"""
MCP Tool: docs.generate

Generate comprehensive documentation from code and contracts.
"""

from typing import Any, Dict
from pathlib import Path

from src.core.analyzers import get_registry
from src.core.project import get_project_paths
from src.core.contract_parser import parse_contract
from src.core.docs_generator import generate_docs, save_docs


async def docs_generate(
    project_path: str,
    feature: str,
    output_dir: str = "docs"
) -> Dict[str, Any]:
    """
    Generate documentation for a feature.

    Combines code analysis with contract information to create
    comprehensive feature documentation in Markdown format.

    Args:
        project_path: Path to CFA project
        feature: Feature name (e.g., "user", "auth")
        output_dir: Directory to save docs (default: "docs")

    Returns:
        Dictionary with:
            - success: Boolean
            - feature: Feature name
            - doc_file: Path to generated documentation
            - content_preview: First 500 chars of documentation
            - sections: List of documentation sections
            - sources: What was used to generate docs

    Example:
        result = await docs_generate(
            project_path="/projects/my-app",
            feature="user",
            output_dir="docs"
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

        # Find implementation file
        impl_file = None
        for ext in [".ts", ".tsx", ".js", ".jsx", ".py", ".rs"]:
            candidate = impl_dir / f"{feature}{ext}"
            if candidate.exists():
                impl_file = candidate
                break

        if not impl_file:
            impl_prefix = impl_dir.relative_to(path)
            return {
                "success": False,
                "error": f"Implementation file not found for feature: {feature}",
                "hint": f"Expected file at {impl_prefix}/{feature}.{{ts|py|rs}}"
            }

        # Analyze implementation
        registry = get_registry()
        analyzer = registry.get_analyzer_for_file(impl_file)

        if not analyzer:
            return {
                "success": False,
                "error": f"No analyzer available for: {impl_file.suffix}"
            }

        try:
            analysis = analyzer.analyze_file(impl_file)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze implementation: {str(e)}"
            }

        # Try to load contract
        contract = None
        contract_file = path / "contracts" / f"{feature}.contract.md"

        if contract_file.exists():
            contract = parse_contract(str(contract_file))

        # Generate documentation
        docs_content = generate_docs(
            file_analysis=analysis,
            contract=contract,
            format="markdown"
        )

        # Save documentation
        output_path = path / output_dir
        doc_file = save_docs(
            docs_content=docs_content,
            output_path=output_path,
            feature_name=feature
        )

        # Extract sections
        sections = _extract_sections(docs_content)

        # Determine sources
        sources = ["code analysis"]
        if contract:
            sources.append("contract")

        return {
            "success": True,
            "feature": feature,
            "doc_file": str(doc_file.relative_to(path)),
            "content_preview": docs_content[:500] + "..." if len(docs_content) > 500 else docs_content,
            "sections": sections,
            "sources": sources,
            "summary": {
                "lines": len(docs_content.split("\n")),
                "characters": len(docs_content),
                "has_contract": contract is not None,
                "exported_functions": len([f for f in analysis.functions if f.is_exported])
            },
            "message": _format_message(feature, doc_file, sources)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Documentation generation failed: {str(e)}"
        }


def _extract_sections(docs_content: str) -> list:
    """Extract section headers from documentation."""
    sections = []
    for line in docs_content.split("\n"):
        if line.startswith("##"):
            section_name = line.strip("#").strip()
            sections.append(section_name)
    return sections


def _format_message(feature: str, doc_file: Path, sources: list) -> str:
    """Generate human-readable message."""
    source_str = " + ".join(sources)
    return f"✓ Generated documentation for '{feature}' from {source_str} → {doc_file.name}"
