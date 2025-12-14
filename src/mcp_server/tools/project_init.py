"""
MCP Tool: project.init

Create a new Context-First Architecture project.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.project import create_project, CFAProject


async def project_init(
    project_path: str,
    name: str,
    description: str = "",
    languages: Optional[List[str]] = None,
    cfa_version: str = "2.0",
    source_root: str = "src"
) -> Dict[str, Any]:
    """
    Create a new CFA project with complete structure.

    Creates (v2.0):
    - .claude/ with map.md, decisions.md, current-task.md, settings.json
    - contracts/ for markdown contracts
    - src/impl/ for feature implementations
    - src/shared/ for types, errors, utils

    Creates (v1.0):
    - .claude/ with map.md, decisions.md, current-task.md
    - contracts/ for markdown contracts
    - impl/ for implementation files (at root)
    - shared/ with types, errors, utils (at root)

    Args:
        project_path: Where to create the project
        name: Project name
        description: Brief description (2-3 sentences max)
        languages: Languages to support (default: ["typescript"])
                   Options: typescript, javascript, python, rust
        cfa_version: CFA version to use (default: "2.0")
                     Options: "2.0" (recommended), "1.0" (legacy)
        source_root: Source root for v2 (default: "src")
                     Only used when cfa_version="2.0"

    Returns:
        Dictionary with:
            - success: Boolean
            - project_path: Full path to created project
            - files_created: List of created files
            - cfa_version: Version used
            - message: Human-readable status

    Example:
        # Create v2 project (recommended)
        result = await project_init(
            project_path="/projects/my-app",
            name="My App",
            description="A REST API for managing tasks",
            languages=["typescript"]
        )

        # Create v1 legacy project
        result = await project_init(
            project_path="/projects/legacy-app",
            name="Legacy App",
            cfa_version="1.0"
        )
    """
    try:
        path = Path(project_path)

        # Check if already exists
        if (path / ".claude").exists():
            return {
                "success": False,
                "error": f"CFA project already exists at {project_path}"
            }

        # Validate languages
        valid_languages = {"typescript", "javascript", "python", "rust"}
        languages = languages or ["typescript"]
        invalid = set(lang.lower() for lang in languages) - valid_languages
        if invalid:
            return {
                "success": False,
                "error": f"Invalid languages: {invalid}. Valid: {valid_languages}"
            }

        # Create project
        project = create_project(
            project_path=project_path,
            name=name,
            description=description,
            languages=[lang.lower() for lang in languages],
            cfa_version=cfa_version,
            source_root=source_root
        )

        # Collect created files
        files_created = []
        for item in path.rglob("*"):
            if item.is_file():
                files_created.append(str(item.relative_to(path)))

        # Version-specific structure description
        if cfa_version.startswith("2"):
            structure_desc = {
                ".claude/": "LLM context (map.md, decisions.md, current-task.md, settings.json)",
                "contracts/": "Markdown contracts (*.contract.md)",
                f"{source_root}/impl/": "Feature implementations",
                f"{source_root}/shared/": "Shared types, errors, utils"
            }
            impl_path = f"{source_root}/impl/"
        else:
            structure_desc = {
                ".claude/": "LLM context (map.md, decisions.md, current-task.md)",
                "contracts/": "Markdown contracts (*.contract.md)",
                "impl/": "Implementation files (complete, not fragmented)",
                "shared/": "Shared types, errors, utils"
            }
            impl_path = "impl/"

        return {
            "success": True,
            "project_path": str(project.path.absolute()),
            "name": project.name,
            "languages": project.languages,
            "cfa_version": project.cfa_version,
            "source_root": project.source_root if cfa_version.startswith("2") else None,
            "files_created": sorted(files_created),
            "structure": structure_desc,
            "next_steps": [
                "1. Read .claude/map.md for project overview",
                "2. Define contracts in contracts/",
                f"3. Implement features in {impl_path}",
                "4. Run project.scan to update map.md"
            ],
            "message": f"✓ CFA v{cfa_version} project '{name}' created successfully"
        }

    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: cannot create project at {project_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create project: {str(e)}"
        }
