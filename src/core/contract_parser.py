"""
Contract parser for Context-First Architecture.

Parses and generates *.contract.md files.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Contract:
    """Represents a parsed contract."""
    name: str
    purpose: str
    language: str = "typescript"
    interface: str = ""
    errors: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    example: str = ""


def parse_contract(contract_path: str) -> Optional[Contract]:
    """
    Parse a *.contract.md file.

    Args:
        contract_path: Path to the contract file

    Returns:
        Contract object if valid, None otherwise
    """
    path = Path(contract_path)

    if not path.exists():
        return None

    content = path.read_text()

    # Extract name from header
    name_match = re.search(r'^#\s+(.+?)\s+Contract', content, re.MULTILINE)
    name = name_match.group(1) if name_match else path.stem.replace(".contract", "")

    # Extract purpose
    purpose = _extract_section(content, "Purpose")

    # Extract interface (code block)
    interface_match = re.search(
        r'## Public Interface\s+```(\w+)\s*(.*?)```',
        content,
        re.DOTALL
    )
    language = interface_match.group(1) if interface_match else "typescript"
    interface = interface_match.group(2).strip() if interface_match else ""

    # Extract errors
    errors_text = _extract_section(content, "Errors This Can Throw")
    errors = _parse_list(errors_text)

    # Extract dependencies
    deps_text = _extract_section(content, "Dependencies")
    dependencies = _parse_list(deps_text)

    # Extract side effects
    effects_text = _extract_section(content, "Side Effects")
    side_effects = _parse_list(effects_text)

    # Extract example
    example_match = re.search(
        r'## Example Usage\s+```\w+\s*(.*?)```',
        content,
        re.DOTALL
    )
    example = example_match.group(1).strip() if example_match else ""

    return Contract(
        name=name,
        purpose=purpose,
        language=language,
        interface=interface,
        errors=errors,
        dependencies=dependencies,
        side_effects=side_effects,
        example=example
    )


def _extract_section(content: str, header: str) -> str:
    """Extract content of a section by header."""
    pattern = rf'## {header}\s*(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_list(text: str) -> List[str]:
    """Parse a markdown list into items."""
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith("* "):
            items.append(line[2:].strip())
    return items


def generate_contract_from_analysis(
    file_analysis: Any,
    name: str,
    purpose: str = ""
) -> Contract:
    """
    Generate a contract from code analysis.

    Args:
        file_analysis: FileAnalysis from analyzer
        name: Contract name
        purpose: Optional purpose description

    Returns:
        Contract object
    """
    # Build interface from exported functions
    interface_lines = []
    for func in file_analysis.functions:
        if func.is_exported:
            interface_lines.append(func.signature)

    # Detect language
    lang_map = {
        "python": "python",
        "typescript": "typescript",
        "javascript": "javascript",
        "rust": "rust"
    }
    language = lang_map.get(file_analysis.language, "typescript")

    # Infer dependencies from imports
    dependencies = []
    for imp in file_analysis.imports:
        if imp.module:
            dependencies.append(f"`{imp.module}` - (imported)")

    return Contract(
        name=name,
        purpose=purpose or f"(Generated from {file_analysis.path})",
        language=language,
        interface="\n".join(interface_lines),
        errors=[],
        dependencies=dependencies,
        side_effects=[],
        example=""
    )


def render_contract(contract: Contract) -> str:
    """Render a Contract to markdown."""

    errors_md = "\n".join(f"- {e}" for e in contract.errors) if contract.errors else "- (none defined)"
    deps_md = "\n".join(f"- {d}" for d in contract.dependencies) if contract.dependencies else "- (none)"
    effects_md = "\n".join(f"- {e}" for e in contract.side_effects) if contract.side_effects else "- (none - pure functions)"

    return f"""# {contract.name} Contract

## Purpose
{contract.purpose}

## Public Interface
```{contract.language}
{contract.interface}
```

## Errors This Can Throw
{errors_md}

## Dependencies
{deps_md}

## Side Effects
{effects_md}

## Example Usage
```{contract.language}
{contract.example or "// TODO: Add usage example"}
```
"""


def validate_contract_vs_impl(
    contract: Contract,
    file_analysis: Any
) -> Dict[str, Any]:
    """
    Validate implementation against contract.

    Args:
        contract: The contract to validate against
        file_analysis: FileAnalysis of the implementation

    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []

    # Extract function names from contract interface
    contract_funcs = set()
    for line in contract.interface.split("\n"):
        # Try to extract function name from various patterns
        match = re.search(r'(?:function|def|fn|const|export)\s+(\w+)', line)
        if match:
            contract_funcs.add(match.group(1))
        # Also try arrow function pattern
        match = re.search(r'(\w+)\s*[=:]\s*(?:async\s*)?\(', line)
        if match:
            contract_funcs.add(match.group(1))

    # Get implemented functions
    impl_funcs = {f.name for f in file_analysis.functions if f.is_exported}

    # Check for missing implementations
    missing = contract_funcs - impl_funcs
    for func in missing:
        issues.append(f"Missing implementation: {func}")

    # Check for extra implementations (not in contract)
    extra = impl_funcs - contract_funcs
    for func in extra:
        warnings.append(f"Not in contract: {func}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "contract_functions": list(contract_funcs),
        "impl_functions": list(impl_funcs)
    }
