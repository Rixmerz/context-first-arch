"""
Documentation generation for Context-First Architecture.

Generates comprehensive documentation from code analysis and contracts.
"""

from typing import Any, Optional
from pathlib import Path


def generate_docs(
    file_analysis: Any,
    contract: Optional[Any] = None,
    format: str = "markdown"
) -> str:
    """
    Generate documentation from file analysis and contract.

    Combines code analysis with contract information to create
    comprehensive feature documentation.

    Args:
        file_analysis: FileAnalysis object
        contract: Optional Contract object
        format: Output format (currently only "markdown")

    Returns:
        Formatted documentation string
    """
    if format != "markdown":
        raise ValueError(f"Unsupported format: {format}")

    sections = []

    # Header
    feature_name = Path(file_analysis.path).stem
    sections.append(f"# {feature_name}\n")

    # Overview
    if contract and contract.purpose:
        sections.append("## Overview\n")
        sections.append(f"{contract.purpose}\n")
    else:
        sections.append("## Overview\n")
        sections.append(f"Documentation for {feature_name}\n")

    # Public API
    sections.append("## Public API\n")
    if contract and contract.interface:
        sections.append(f"```{contract.language}")
        sections.append(contract.interface)
        sections.append("```\n")
    else:
        # Generate from analysis
        api_docs = _format_api_from_analysis(file_analysis)
        sections.append(api_docs)

    # Functions
    if file_analysis.functions:
        sections.append("## Functions\n")
        for func in file_analysis.functions:
            if func.is_exported:
                sections.append(f"### `{func.name}`\n")

                if func.docstring:
                    sections.append(f"{func.docstring}\n")

                sections.append(f"**Signature**: `{func.signature}`\n")

                if func.parameters:
                    sections.append("**Parameters**:")
                    for param in func.parameters:
                        param_name = param.get("name", "")
                        param_type = param.get("type", "any")
                        sections.append(f"- `{param_name}`: {param_type}")
                    sections.append("")

                if func.return_type:
                    sections.append(f"**Returns**: `{func.return_type}`\n")

    # Dependencies
    sections.append("## Dependencies\n")
    if contract and contract.dependencies:
        for dep in contract.dependencies:
            sections.append(f"- {dep}")
        sections.append("")
    elif file_analysis.imports:
        sections.append(_format_dependencies(file_analysis.imports))
    else:
        sections.append("- (no external dependencies)\n")

    # Errors
    if contract and contract.errors:
        sections.append("## Errors\n")
        for error in contract.errors:
            sections.append(f"- {error}")
        sections.append("")

    # Side Effects
    if contract and contract.side_effects:
        sections.append("## Side Effects\n")
        for effect in contract.side_effects:
            sections.append(f"- {effect}")
        sections.append("")

    # Types
    if file_analysis.types:
        sections.append("## Types\n")
        for type_name in file_analysis.types:
            sections.append(f"- `{type_name}`")
        sections.append("")

    # Example Usage
    if contract and contract.example:
        sections.append("## Example Usage\n")
        sections.append(f"```{contract.language}")
        sections.append(contract.example)
        sections.append("```\n")

    return "\n".join(sections)


def _format_api_from_analysis(analysis: Any) -> str:
    """Format API documentation from file analysis."""
    lines = []

    if analysis.exports:
        lines.append("**Exports**:")
        for export in analysis.exports[:20]:  # Limit to 20
            lines.append(f"- `{export}`")
        lines.append("")

    if analysis.functions:
        exported_funcs = [f for f in analysis.functions if f.is_exported]
        if exported_funcs:
            lines.append("**Functions**:")
            for func in exported_funcs:
                lines.append(f"- `{func.signature}`")
            lines.append("")

    return "\n".join(lines) if lines else "- (no public API defined)\n"


def _format_dependencies(imports: list) -> str:
    """Format dependencies from imports."""
    lines = []

    # Group by external vs internal
    external = []
    internal = []

    for imp in imports:
        module = imp.module
        if module.startswith(".") or module.startswith("/"):
            internal.append(module)
        else:
            external.append(module)

    if external:
        lines.append("**External**:")
        for mod in sorted(set(external))[:20]:
            lines.append(f"- `{mod}`")
        lines.append("")

    if internal:
        lines.append("**Internal**:")
        for mod in sorted(set(internal))[:20]:
            lines.append(f"- `{mod}`")
        lines.append("")

    return "\n".join(lines) if lines else "- (no dependencies)\n"


def save_docs(
    docs_content: str,
    output_path: Path,
    feature_name: str
) -> Path:
    """
    Save generated documentation to file.

    Args:
        docs_content: Documentation content
        output_path: Directory to save docs
        feature_name: Feature name for filename

    Returns:
        Path to saved documentation file
    """
    # Create docs directory if needed
    output_path.mkdir(parents=True, exist_ok=True)

    # Save documentation
    doc_file = output_path / f"{feature_name}.md"
    doc_file.write_text(docs_content)

    return doc_file
