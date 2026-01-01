"""
Project structure management for Context-First Architecture.

CFA v2 supports flexible source organization:
- .claude/ for LLM context (map.md, decisions.md, current-task.md, settings.json)
- contracts/ for markdown contracts
- src/impl/ for feature implementations (configurable via source_root)
- src/shared/ for types, errors, utils
- src/app/ for application layer (optional)

Legacy v1 structure (impl/ at root) is still supported.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class CFAProject:
    """Represents a Context-First Architecture project."""
    path: Path
    name: str
    description: str
    languages: List[str]
    created_at: datetime
    cfa_version: str = "2.0"
    source_root: str = "src"
    _settings: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def claude_dir(self) -> Path:
        return self.path / ".claude"

    @property
    def contracts_dir(self) -> Path:
        return self.path / "contracts"

    @property
    def impl_dir(self) -> Path:
        """Get impl directory based on CFA version and source_root setting."""
        # v3: src/features/ (feature-based architecture)
        if self.cfa_version.startswith("3"):
            return self.path / self.source_root / "features"
        # v2: src/impl/ (or custom source_root)
        if self.cfa_version.startswith("2"):
            return self.path / self.source_root / "impl"
        # v1 legacy: impl/ at root
        return self.path / "impl"

    @property
    def features_dir(self) -> Path:
        """Get features directory (CFA v3 only)."""
        return self.path / self.source_root / "features"

    @property
    def shared_dir(self) -> Path:
        """Get shared directory based on CFA version."""
        if self.cfa_version.startswith("2") or self.cfa_version.startswith("3"):
            return self.path / self.source_root / "shared"
        return self.path / "shared"

    @property
    def app_dir(self) -> Path:
        """Get application layer directory (v2/v3 only)."""
        return self.path / self.source_root / "app"

    @property
    def map_file(self) -> Path:
        return self.claude_dir / "map.md"

    @property
    def decisions_file(self) -> Path:
        return self.claude_dir / "decisions.md"

    @property
    def task_file(self) -> Path:
        return self.claude_dir / "current-task.md"

    @property
    def settings_file(self) -> Path:
        return self.claude_dir / "settings.json"


def create_project(
    project_path: str,
    name: str,
    description: str = "",
    languages: Optional[List[str]] = None,
    cfa_version: str = "2.0",
    source_root: str = "src"
) -> CFAProject:
    """
    Create a new CFA project with complete structure.

    Args:
        project_path: Where to create the project
        name: Project name
        description: Brief project description
        languages: List of languages (e.g., ["typescript", "python"])
        cfa_version: CFA version ("2.0" or "1.0", default: "2.0")
        source_root: Source root directory for v2 (default: "src")

    Returns:
        CFAProject instance
    """
    path = Path(project_path)
    languages = languages or ["typescript"]

    # Create directory structure based on version
    if cfa_version.startswith("2"):
        # v2: .claude/, contracts/ at root, impl/shared in src/
        directories = [
            path / ".claude",
            path / "contracts",
            path / source_root / "impl",
            path / source_root / "shared",
        ]
    else:
        # v1 legacy: impl/shared at root
        directories = [
            path / ".claude",
            path / "contracts",
            path / "impl",
            path / "shared",
        ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Load templates - templates/ is at project root (not src/templates/)
    # Path: src/core/project.py -> src/core -> src -> project_root/templates
    template_dir = Path(__file__).parent.parent.parent / "templates"

    # Create map.md
    map_template = (template_dir / "map.md.template").read_text()
    impl_path = f"{source_root}/impl" if cfa_version.startswith("2") else "impl"
    map_content = map_template.format(
        description=description or f"{name} - A Context-First Architecture project (CFA v{cfa_version})",
        entry_points=f"- `{impl_path}/main.{_get_extension(languages[0])}:main()` → Application entry",
        data_flow="[Input] → [Process] → [Output]",
        file_index="| (no files yet) | | |",
        current_state="- ⏳ Initial setup",
        non_obvious="(none yet)"
    )
    (path / ".claude" / "map.md").write_text(map_content)

    # Create decisions.md
    decisions_template = (template_dir / "decisions.md.template").read_text()
    decisions_content = decisions_template.format(
        decisions=f"## {datetime.now().strftime('%Y-%m-%d')}: Project initialized with CFA\n"
                  f"**Context**: Starting new project\n"
                  f"**Decision**: Use Context-First Architecture\n"
                  f"**Reason**: Optimized for LLM-assisted development\n"
    )
    (path / ".claude" / "decisions.md").write_text(decisions_content)

    # Create current-task.md
    task_template = (template_dir / "current-task.md.template").read_text()
    task_content = task_template.format(
        goal="Initial project setup",
        status="NOT_STARTED",
        completed="(none)",
        files_modified="(none)",
        blockers="None",
        next_steps="1. Define project contracts\n2. Implement core functionality",
        context="Fresh project, no existing code"
    )
    (path / ".claude" / "current-task.md").write_text(task_content)

    # Create shared files based on language
    shared_path = path / source_root / "shared" if cfa_version.startswith("2") else path / "shared"
    _create_shared_files(shared_path, languages)

    # Create settings.json (v2 configuration)
    settings = {
        "cfa_version": cfa_version,
        "source_root": source_root if cfa_version.startswith("2") else "",
        "framework": "",  # Can be set later: react, next, express, fastapi, etc.
        "project_type": "",  # frontend, backend, fullstack, microservice
    }
    (path / ".claude" / "settings.json").write_text(
        json.dumps(settings, indent=2)
    )

    # Create project config (legacy compatibility)
    config = {
        "name": name,
        "description": description,
        "languages": languages,
        "created_at": datetime.now().isoformat(),
        "cfa_version": cfa_version
    }
    (path / ".claude" / "config.json").write_text(
        json.dumps(config, indent=2)
    )

    return CFAProject(
        path=path,
        name=name,
        description=description,
        languages=languages,
        created_at=datetime.now(),
        cfa_version=cfa_version,
        source_root=source_root,
        _settings=settings
    )


def load_project(project_path: str) -> Optional[CFAProject]:
    """
    Load an existing CFA project.

    Args:
        project_path: Path to the project

    Returns:
        CFAProject if valid, None otherwise
    """
    path = Path(project_path)
    config_file = path / ".claude" / "config.json"
    settings_file = path / ".claude" / "settings.json"

    if not config_file.exists():
        return None

    try:
        # Load config.json
        config = json.loads(config_file.read_text())

        # Load settings.json (v2) or use defaults
        cfa_version = "1.0"
        source_root = ""
        settings = {}

        if settings_file.exists():
            try:
                settings = json.loads(settings_file.read_text())
                cfa_version = settings.get("cfa_version", "2.0")
                source_root = settings.get("source_root", "src")
            except json.JSONDecodeError:
                pass
        else:
            # Fallback: check config.json for cfa_version
            cfa_version = config.get("cfa_version", "1.0")
            # v1 has no source_root, v2 defaults to "src"
            source_root = "src" if cfa_version.startswith("2") else ""

        return CFAProject(
            path=path,
            name=config["name"],
            description=config.get("description", ""),
            languages=config.get("languages", ["typescript"]),
            created_at=datetime.fromisoformat(config["created_at"]),
            cfa_version=cfa_version,
            source_root=source_root,
            _settings=settings
        )
    except (json.JSONDecodeError, KeyError):
        return None


def validate_project(project_path: str) -> Dict[str, Any]:
    """
    Validate a CFA project structure (supports v1 and v2).

    Returns dict with:
        - valid: bool
        - errors: List of structural errors
        - warnings: List of recommendations
        - version: Detected CFA version
    """
    path = Path(project_path)
    errors = []
    warnings = []

    # Load project to detect version
    project = load_project(project_path)
    version = project.cfa_version if project else "unknown"

    # Required directories (invariants)
    required_dirs = [".claude", "contracts"]
    for dir_name in required_dirs:
        if not (path / dir_name).is_dir():
            errors.append(f"Missing required directory: {dir_name}/")

    # Version-specific directory checks
    if project:
        if not project.impl_dir.exists():
            errors.append(f"Missing impl directory: {project.impl_dir.relative_to(path)}/")
        if not project.shared_dir.exists():
            errors.append(f"Missing shared directory: {project.shared_dir.relative_to(path)}/")
    else:
        # No config, check both possible locations
        if not (path / "impl").exists() and not (path / "src" / "impl").exists():
            errors.append("Missing impl directory (checked root and src/)")

    # Required files in .claude/
    required_files = ["map.md", "decisions.md", "current-task.md", "config.json"]
    for file_name in required_files:
        if not (path / ".claude" / file_name).exists():
            errors.append(f"Missing required file: .claude/{file_name}")

    # v2 should have settings.json
    if version.startswith("2") and not (path / ".claude" / "settings.json").exists():
        warnings.append("CFA v2 project should have .claude/settings.json")

    # Check for deep nesting (more than 3 levels in impl/)
    if project and project.impl_dir.exists():
        for item in project.impl_dir.rglob("*"):
            if item.is_file():
                relative = item.relative_to(project.impl_dir)
                depth = len(relative.parts)
                if depth > 2:  # impl/feature/file.ts is OK, impl/a/b/c/file.ts is not
                    warnings.append(f"Deep nesting in impl: {relative} ({depth} levels)")

    # Check for fragmented files
    if project and project.impl_dir.exists():
        for impl_file in project.impl_dir.rglob("*"):
            if impl_file.is_file() and impl_file.suffix in [".ts", ".js", ".py", ".rs"]:
                try:
                    lines = len(impl_file.read_text().splitlines())
                    if lines < 20:
                        warnings.append(f"Potentially fragmented file: {impl_file.relative_to(path)} ({lines} lines)")
                except Exception:
                    pass

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "version": version
    }


def get_project_paths(project_path: str | Path) -> Dict[str, Path]:
    """
    Get standardized paths for a CFA project.

    This is the recommended way for tools to access project directories.
    Automatically handles v1, v2, and v3 structures.

    Args:
        project_path: Path to CFA project

    Returns:
        Dictionary with paths:
            - root: Project root
            - impl_dir: Implementation directory (features_dir for v3)
            - shared_dir: Shared code directory
            - contracts_dir: Contracts directory
            - claude_dir: .claude directory
            - features_dir: Features directory (v3 only, alias of impl_dir)

    Example:
        paths = get_project_paths("/path/to/project")
        impl_dir = paths["impl_dir"]  # Works for v1, v2, and v3
    """
    path = Path(project_path)

    # Try to load project for accurate paths
    project = load_project(str(path))

    if project:
        paths = {
            "root": path,
            "impl_dir": project.impl_dir,
            "shared_dir": project.shared_dir,
            "contracts_dir": project.contracts_dir,
            "claude_dir": project.claude_dir,
        }
        # Add features_dir for v3 projects
        if project.cfa_version.startswith("3"):
            paths["features_dir"] = project.features_dir
        return paths

    # Fallback: Detect structure by checking what exists
    if (path / "src" / "features").exists():
        # v3 structure (feature-based)
        return {
            "root": path,
            "impl_dir": path / "src" / "features",
            "features_dir": path / "src" / "features",
            "shared_dir": path / "src" / "shared",
            "contracts_dir": path / "contracts",
            "claude_dir": path / ".claude",
        }
    elif (path / "src" / "impl").exists():
        # v2 structure
        return {
            "root": path,
            "impl_dir": path / "src" / "impl",
            "shared_dir": path / "src" / "shared",
            "contracts_dir": path / "contracts",
            "claude_dir": path / ".claude",
        }
    else:
        # v1 structure (default)
        return {
            "root": path,
            "impl_dir": path / "impl",
            "shared_dir": path / "shared",
            "contracts_dir": path / "contracts",
            "claude_dir": path / ".claude",
        }


def _get_extension(language: str) -> str:
    """Get file extension for a language."""
    extensions = {
        "typescript": "ts",
        "javascript": "js",
        "python": "py",
        "rust": "rs"
    }
    return extensions.get(language.lower(), "ts")


def _create_shared_files(shared_dir: Path, languages: List[str]):
    """Create shared files for the primary language."""
    lang = languages[0].lower()
    ext = _get_extension(lang)

    if lang in ["typescript", "javascript"]:
        # types.ts
        (shared_dir / f"types.{ext}").write_text(
            "// ============ SHARED TYPES ============\n\n"
            "// Add your shared type definitions here\n"
            "// Keep all types in ONE file for easy LLM access\n\n"
            "export interface Example {\n"
            "  id: string;\n"
            "  name: string;\n"
            "}\n"
        )

        # errors.ts
        (shared_dir / f"errors.{ext}").write_text(
            "// ============ SHARED ERRORS ============\n\n"
            "// Custom error classes for the project\n"
            "// Keep all errors in ONE file for easy discovery\n\n"
            "export class AppError extends Error {\n"
            "  constructor(message: string, public code: string) {\n"
            "    super(message);\n"
            "    this.name = 'AppError';\n"
            "  }\n"
            "}\n\n"
            "export class NotFoundError extends AppError {\n"
            "  constructor(resource: string) {\n"
            "    super(`${resource} not found`, 'NOT_FOUND');\n"
            "    this.name = 'NotFoundError';\n"
            "  }\n"
            "}\n"
        )

        # utils.ts
        (shared_dir / f"utils.{ext}").write_text(
            "// ============ SHARED UTILITIES ============\n\n"
            "// Utility functions used across the project\n"
            "// Keep utilities in ONE file, organized by section\n\n"
            "// --- String Utils ---\n\n"
            "export function capitalize(str: string): string {\n"
            "  return str.charAt(0).toUpperCase() + str.slice(1);\n"
            "}\n\n"
            "// --- Date Utils ---\n\n"
            "export function formatDate(date: Date): string {\n"
            "  return date.toISOString().split('T')[0];\n"
            "}\n"
        )

    elif lang == "python":
        # types.py
        (shared_dir / "types.py").write_text(
            '"""Shared type definitions."""\n\n'
            "from dataclasses import dataclass\n"
            "from typing import Optional\n\n\n"
            "@dataclass\n"
            "class Example:\n"
            '    """Example shared type."""\n'
            "    id: str\n"
            "    name: str\n"
        )

        # errors.py
        (shared_dir / "errors.py").write_text(
            '"""Shared error classes."""\n\n\n'
            "class AppError(Exception):\n"
            '    """Base application error."""\n'
            "    def __init__(self, message: str, code: str):\n"
            "        super().__init__(message)\n"
            "        self.code = code\n\n\n"
            "class NotFoundError(AppError):\n"
            '    """Resource not found error."""\n'
            "    def __init__(self, resource: str):\n"
            '        super().__init__(f"{resource} not found", "NOT_FOUND")\n'
        )

        # utils.py
        (shared_dir / "utils.py").write_text(
            '"""Shared utility functions."""\n\n'
            "from datetime import datetime\n\n\n"
            "# --- String Utils ---\n\n"
            "def capitalize(s: str) -> str:\n"
            '    """Capitalize first letter."""\n'
            "    return s[0].upper() + s[1:] if s else s\n\n\n"
            "# --- Date Utils ---\n\n"
            "def format_date(date: datetime) -> str:\n"
            '    """Format date as YYYY-MM-DD."""\n'
            '    return date.strftime("%Y-%m-%d")\n'
        )

    elif lang == "rust":
        # types.rs
        (shared_dir / "types.rs").write_text(
            "//! Shared type definitions\n\n"
            "/// Example shared type\n"
            "#[derive(Debug, Clone)]\n"
            "pub struct Example {\n"
            "    pub id: String,\n"
            "    pub name: String,\n"
            "}\n"
        )

        # errors.rs
        (shared_dir / "errors.rs").write_text(
            "//! Shared error types\n\n"
            "use std::fmt;\n\n"
            "#[derive(Debug)]\n"
            "pub enum AppError {\n"
            "    NotFound(String),\n"
            "    InvalidInput(String),\n"
            "}\n\n"
            "impl fmt::Display for AppError {\n"
            "    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {\n"
            "        match self {\n"
            '            AppError::NotFound(r) => write!(f, "{} not found", r),\n'
            '            AppError::InvalidInput(m) => write!(f, "Invalid input: {}", m),\n'
            "        }\n"
            "    }\n"
            "}\n\n"
            "impl std::error::Error for AppError {}\n"
        )

        # utils.rs
        (shared_dir / "utils.rs").write_text(
            "//! Shared utility functions\n\n"
            "/// Capitalize first letter of a string\n"
            "pub fn capitalize(s: &str) -> String {\n"
            "    let mut chars = s.chars();\n"
            "    match chars.next() {\n"
            "        None => String::new(),\n"
            "        Some(c) => c.to_uppercase().chain(chars).collect(),\n"
            "    }\n"
            "}\n"
        )
