"""
Framework-Agnostic CFA Transformation Rules

Supports:
- Next.js (app/, pages/)
- Vite/React (src/)
- Remix (app/)
- Generic React projects
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum
import os
import json


class ConsolidationStrategy(Enum):
    """How to consolidate multiple files into one"""
    MERGE_WITH_SECTIONS = "merge_with_sections"
    MERGE_EXPORTS = "merge_exports"
    GROUP_BY_RESOURCE = "group_by_resource"


@dataclass
class ProjectStructure:
    """Detected project structure"""
    framework: str  # nextjs, vite, react, remix
    source_root: str  # src, app, or root
    has_typescript: bool
    components_dir: Optional[str]
    api_dir: Optional[str]
    types_dir: Optional[str]
    utils_dir: Optional[str]


def detect_project_structure(project_path: str) -> ProjectStructure:
    """Auto-detect project structure and framework"""

    # Read package.json
    package_json_path = os.path.join(project_path, "package.json")
    framework = "unknown"
    deps = {}

    if os.path.exists(package_json_path):
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
            deps = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {})
            }

    # Detect framework
    if "next" in deps:
        framework = "nextjs"
    elif "vite" in deps:
        framework = "vite"
    elif "@remix-run/react" in deps:
        framework = "remix"
    elif "react" in deps:
        framework = "react"

    # Detect source root
    if os.path.exists(os.path.join(project_path, "src")):
        source_root = "src"
    elif os.path.exists(os.path.join(project_path, "app")) and framework in ["nextjs", "remix"]:
        source_root = "app"
    else:
        source_root = ""  # Root level

    # Detect TypeScript
    has_typescript = os.path.exists(os.path.join(project_path, "tsconfig.json"))

    # Detect specific directories
    def find_dir(names: List[str]) -> Optional[str]:
        for name in names:
            if source_root:
                path = os.path.join(project_path, source_root, name)
            else:
                path = os.path.join(project_path, name)
            if os.path.exists(path):
                return f"{source_root}/{name}" if source_root else name
        return None

    components_dir = find_dir(["components"])
    api_dir = find_dir(["api"])
    types_dir = find_dir(["types"])
    utils_dir = find_dir(["utils", "lib"])

    return ProjectStructure(
        framework=framework,
        source_root=source_root,
        has_typescript=has_typescript,
        components_dir=components_dir,
        api_dir=api_dir,
        types_dir=types_dir,
        utils_dir=utils_dir,
    )


def get_transformation_patterns(structure: ProjectStructure) -> Dict[str, List[str]]:
    """
    Generate glob patterns for transformations based on detected structure

    Returns dict with keys:
    - types: Patterns for type files
    - utils: Patterns for utility files
    - errors: Patterns for error files
    - components: Patterns for component files
    - api: Patterns for API files
    - ui: Patterns for UI library components
    """
    root = structure.source_root

    patterns = {
        "types": [
            f"{root}/**/*.types.ts" if root else "**/*.types.ts",
            f"{root}/types/**/*.ts" if root else "types/**/*.ts",
            "**/types.ts",
        ],
        "utils": [
            f"{root}/utils/**/*.ts" if root else "utils/**/*.ts",
            f"{root}/lib/**/*.ts" if root else "lib/**/*.ts",
            "**/utils.ts",
        ],
        "errors": [
            f"{root}/**/errors.ts" if root else "**/errors.ts",
            f"{root}/**/*-error.ts" if root else "**/*-error.ts",
        ],
        "db": [
            f"{root}/lib/db.ts" if root else "lib/db.ts",
            f"{root}/lib/database.ts" if root else "lib/database.ts",
            f"{root}/lib/prisma.ts" if root else "lib/prisma.ts",
        ],
        "ui": [
            f"{root}/components/ui/**/*.tsx" if root else "components/ui/**/*.tsx",
        ],
        "components": [
            f"{root}/components/**/*.tsx" if root else "components/**/*.tsx",
        ],
        "api": [
            f"{root}/api/**/*.ts" if root else "api/**/*.ts",
        ],
    }

    # For Next.js App Router, adjust paths
    if structure.framework == "nextjs" and structure.source_root == "app":
        patterns["api"] = [
            "app/api/**/route.ts",
        ]

    return patterns


# ============================================================================
# FEATURE DETECTION
# ============================================================================

COMPONENT_FEATURE_MAP = {
    "login": "auth",
    "signup": "auth",
    "auth": "auth",
    "forgotpassword": "auth",
    "resetpassword": "auth",
    "user": "user",
    "profile": "user",
    "account": "user",
    "dashboard": "dashboard",
    "settings": "settings",
    "invoice": "invoice",
    "payment": "payment",
    "product": "product",
    "cart": "cart",
    "checkout": "checkout",
}


def detect_feature_from_filename(filename: str) -> str:
    """
    Extract feature name from filename

    Examples:
        LoginForm.tsx → auth
        UserCard.tsx → user
        ProductList.tsx → product
    """
    filename_lower = filename.lower()

    for pattern, feature in COMPONENT_FEATURE_MAP.items():
        if pattern in filename_lower:
            return feature

    # Default: extract first word
    import re
    match = re.match(r'([A-Z][a-z]+)', filename)
    if match:
        return match.group(1).lower()

    return "misc"


# ============================================================================
# FILES TO PRESERVE
# ============================================================================

def get_preserve_patterns(structure: ProjectStructure) -> List[str]:
    """Get patterns for files that should NOT be transformed"""

    patterns = [
        "package.json",
        "tsconfig.json",
        "next.config.*",
        "vite.config.*",
        "tailwind.config.*",
        "postcss.config.*",
        ".env*",
        "public/**/*",
        "*.config.*",
        "README.md",
    ]

    # Framework-specific preserves
    if structure.framework == "nextjs":
        patterns.extend([
            "app/page.tsx",
            "app/layout.tsx",
            "app/globals.css",
            "app/**/page.tsx",
            "app/**/layout.tsx",
            "app/**/loading.tsx",
            "app/**/error.tsx",
            "app/**/not-found.tsx",
            "middleware.ts",
        ])
    elif structure.framework in ["vite", "react"]:
        patterns.extend([
            "src/main.tsx",
            "src/App.tsx",
            "src/index.css",
            "index.html",
        ])

    return patterns


# ============================================================================
# CONSOLIDATION TEMPLATES
# ============================================================================

COMPONENT_TEMPLATE = """// {filename}
// Consolidated {feature} components
// CFA: All {feature}-related UI components in one file for efficient LLM navigation

import React from 'react';
// Import types from shared/types.ts
// Example: import {{ User, AuthResponse }} from '@/shared/types';

// ============================================================================
// {section_names}
// ============================================================================

{content}

"""

API_TEMPLATE = """// {filename}
// API routes for {resource}
// CFA: All {resource} CRUD operations in one file

import {{ NextRequest, NextResponse }} from 'next/server';
// Import types from shared/types.ts

// ============================================================================
// HANDLERS
// ============================================================================

{content}

"""

TYPES_TEMPLATE = """// shared/types.ts
// All TypeScript type definitions
// CFA: Single source of truth for types - easier for LLMs to navigate

{content}

"""

UTILS_TEMPLATE = """// shared/utils.ts
// Utility functions
// CFA: All utility functions in one file for efficient context loading

{content}

"""
