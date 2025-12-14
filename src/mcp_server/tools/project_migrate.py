"""
MCP Tool: project.migrate

Convert existing project to CFA structure.
"""

from typing import Any, Dict, Optional
from pathlib import Path

from src.core.migrator import plan_migration, execute_migration


async def project_migrate(
    source_path: str,
    target_path: str,
    name: Optional[str] = None,
    description: str = "",
    include_tests: bool = True
) -> Dict[str, Any]:
    """
    Migrate an existing project to CFA structure.

    This tool:
    1. Analyzes the source project structure
    2. Creates a new CFA project at target_path
    3. Flattens nested files into impl/
    4. Consolidates types into shared/types.*
    5. Generates contracts from code analysis
    6. Creates map.md from project analysis

    NOTE: Source project is NOT modified. Creates a copy.

    Args:
        source_path: Path to existing project
        target_path: Where to create CFA project (must not exist)
        name: Project name (defaults to source folder name)
        description: Project description for map.md
        include_tests: Whether to migrate test files (default: true)

    Returns:
        Dictionary with:
            - success: Boolean
            - stats: Migration statistics
            - warnings: Any issues encountered
            - next_steps: What to do after migration

    Example:
        result = await project_migrate(
            source_path="/projects/old-app",
            target_path="/projects/old-app-cfa",
            name="My App",
            description="REST API for task management"
        )
    """
    try:
        source = Path(source_path)
        target = Path(target_path)

        if not source.exists():
            return {
                "success": False,
                "error": f"Source not found: {source_path}"
            }

        if target.exists():
            return {
                "success": False,
                "error": f"Target already exists: {target_path}. Choose a new location."
            }

        # Create migration plan
        plan = plan_migration(
            source_path=source_path,
            target_path=target_path,
            include_tests=include_tests
        )

        # Execute migration
        project_name = name or source.name
        result = execute_migration(
            plan=plan,
            project_name=project_name,
            description=description
        )

        if not result.success:
            return {
                "success": False,
                "error": result.errors[0] if result.errors else "Migration failed"
            }

        return {
            "success": True,
            "target_path": result.target_path,
            "stats": {
                "files_migrated": result.files_migrated,
                "contracts_generated": result.contracts_generated,
                "languages_detected": plan.languages,
                "source_files": len(plan.files_to_migrate),
                "type_files_consolidated": len(plan.type_files),
                "test_files": len(plan.test_files)
            },
            "warnings": result.warnings,
            "structure": {
                ".claude/": "map.md, decisions.md, current-task.md created",
                "contracts/": f"{result.contracts_generated} contracts generated",
                "impl/": "Implementation files (flattened)",
                "shared/": "Types, errors, utils"
            },
            "next_steps": [
                "1. Review .claude/map.md for project overview",
                "2. Check generated contracts in contracts/",
                "3. Edit contracts to add errors, side effects, examples",
                "4. Run project.scan to refresh map.md",
                "5. Delete source project when migration verified"
            ],
            "message": f"Migration complete: {result.files_migrated} files, {result.contracts_generated} contracts"
        }

    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied accessing paths"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Migration failed: {str(e)}"
        }
