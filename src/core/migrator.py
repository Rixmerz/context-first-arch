"""
Project migrator for Context-First Architecture.

Converts existing projects to CFA structure.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import shutil

from src.core.project import create_project, _get_extension
from src.core.analyzers import get_registry
from src.core.map_generator import generate_map, render_map
from src.core.contract_parser import generate_contract_from_analysis, render_contract


@dataclass
class MigrationPlan:
    """Plan for migrating a project."""
    source_path: Path
    target_path: Path
    languages: List[str]
    files_to_migrate: List[Path]
    type_files: List[Path]
    test_files: List[Path]
    contracts_to_generate: List[str]


@dataclass
class MigrationResult:
    """Result of a migration."""
    success: bool
    target_path: str
    files_migrated: int
    contracts_generated: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def plan_migration(
    source_path: str,
    target_path: str,
    include_tests: bool = True
) -> MigrationPlan:
    """
    Create a migration plan for an existing project.

    Args:
        source_path: Path to existing project
        target_path: Where to create CFA project
        include_tests: Whether to migrate test files

    Returns:
        MigrationPlan with analysis of what to migrate
    """
    source = Path(source_path)
    target = Path(target_path)
    registry = get_registry()

    languages: Set[str] = set()
    files_to_migrate: List[Path] = []
    type_files: List[Path] = []
    test_files: List[Path] = []

    # Scan source for code files
    for file_path in source.rglob("*"):
        if file_path.is_file():
            # Skip common non-code directories
            rel_parts = file_path.relative_to(source).parts
            if any(p in rel_parts for p in [
                "node_modules", ".git", "__pycache__", "target",
                "dist", "build", ".next", "coverage", "venv", ".venv"
            ]):
                continue

            analyzer = registry.get_analyzer_for_file(file_path)
            if analyzer:
                languages.add(analyzer.language)

                # Categorize files
                filename_lower = file_path.name.lower()
                if ".test." in filename_lower or "_test." in filename_lower or filename_lower.startswith("test_"):
                    if include_tests:
                        test_files.append(file_path)
                elif "type" in filename_lower or ".d.ts" in filename_lower:
                    type_files.append(file_path)
                else:
                    files_to_migrate.append(file_path)

    # Determine contracts to generate (one per significant file)
    contracts_to_generate = []
    for f in files_to_migrate:
        if not any(skip in f.name.lower() for skip in ["index", "main", "app", "config"]):
            contracts_to_generate.append(f.stem)

    return MigrationPlan(
        source_path=source,
        target_path=target,
        languages=list(languages) or ["typescript"],
        files_to_migrate=files_to_migrate,
        type_files=type_files,
        test_files=test_files,
        contracts_to_generate=contracts_to_generate[:10]  # Limit initial contracts
    )


def execute_migration(
    plan: MigrationPlan,
    project_name: str,
    description: str = ""
) -> MigrationResult:
    """
    Execute a migration plan.

    Args:
        plan: The migration plan to execute
        project_name: Name for the new project
        description: Project description

    Returns:
        MigrationResult with details
    """
    warnings = []
    errors = []
    registry = get_registry()

    try:
        # Create CFA project structure
        create_project(
            project_path=str(plan.target_path),
            name=project_name,
            description=description,
            languages=plan.languages
        )

        impl_dir = plan.target_path / "impl"
        shared_dir = plan.target_path / "shared"
        contracts_dir = plan.target_path / "contracts"

        files_migrated = 0
        contracts_generated = 0

        # Migrate main implementation files
        for src_file in plan.files_to_migrate:
            try:
                # Determine target location
                dest_name = _sanitize_filename(src_file)
                dest_path = impl_dir / dest_name

                # Copy file
                shutil.copy2(src_file, dest_path)
                files_migrated += 1

            except Exception as e:
                warnings.append(f"Failed to migrate {src_file.name}: {e}")

        # Consolidate type files into shared/types.*
        if plan.type_files:
            _consolidate_types(plan.type_files, shared_dir, plan.languages[0])
            files_migrated += len(plan.type_files)

        # Migrate test files
        for test_file in plan.test_files:
            try:
                dest_name = _sanitize_filename(test_file)
                dest_path = impl_dir / dest_name
                shutil.copy2(test_file, dest_path)
                files_migrated += 1
            except Exception as e:
                warnings.append(f"Failed to migrate test {test_file.name}: {e}")

        # Generate contracts from migrated files
        for contract_name in plan.contracts_to_generate:
            ext = _get_extension(plan.languages[0])
            impl_file = impl_dir / f"{contract_name}.{ext}"

            if impl_file.exists():
                try:
                    analyzer = registry.get_analyzer_for_file(impl_file)
                    if analyzer:
                        analysis = analyzer.analyze_file(impl_file)
                        contract = generate_contract_from_analysis(
                            analysis,
                            name=contract_name.replace("_", " ").title()
                        )
                        contract_content = render_contract(contract)
                        contract_file = contracts_dir / f"{contract_name}.contract.md"
                        contract_file.write_text(contract_content)
                        contracts_generated += 1
                except Exception as e:
                    warnings.append(f"Failed to generate contract for {contract_name}: {e}")

        # Generate map.md
        try:
            project_map = generate_map(str(plan.target_path))
            project_map.description = description or f"Migrated from {plan.source_path.name}"
            map_content = render_map(project_map)
            (plan.target_path / ".claude" / "map.md").write_text(map_content)
        except Exception as e:
            warnings.append(f"Failed to generate map: {e}")

        return MigrationResult(
            success=True,
            target_path=str(plan.target_path),
            files_migrated=files_migrated,
            contracts_generated=contracts_generated,
            warnings=warnings,
            errors=errors
        )

    except Exception as e:
        return MigrationResult(
            success=False,
            target_path=str(plan.target_path),
            files_migrated=0,
            contracts_generated=0,
            errors=[str(e)]
        )


def _sanitize_filename(file_path: Path) -> str:
    """Create a flat filename from a nested path."""
    # Get relative path parts (excluding common directories)
    parts = []
    for part in file_path.parts:
        if part not in ["src", "lib", "source", "app", "components"]:
            parts.append(part)

    # If deeply nested, flatten with hyphens
    if len(parts) > 2:
        name = "-".join(parts[-2:])  # Last two parts
    else:
        name = file_path.name

    return name


def _consolidate_types(
    type_files: List[Path],
    shared_dir: Path,
    language: str
) -> None:
    """Consolidate type files into shared/types.*"""
    ext = _get_extension(language)
    types_file = shared_dir / f"types.{ext}"

    # Read existing types file
    existing_content = types_file.read_text() if types_file.exists() else ""

    # Append content from type files
    consolidated = [existing_content, "\n// ============ MIGRATED TYPES ============\n"]

    for type_file in type_files:
        try:
            content = type_file.read_text()
            # Add source comment
            consolidated.append(f"\n// From: {type_file.name}\n")
            consolidated.append(content)
        except Exception:
            pass

    types_file.write_text("\n".join(consolidated))
