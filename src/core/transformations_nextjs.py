"""
Framework to CFA Transformation Rules

Defines how to convert standard framework structures (Next.js, Vite, React, etc.) to CFA.
Supports multiple source directory conventions:
- Next.js: app/, pages/
- Vite/React: src/
- Remix: app/
- Custom: lib/, components/
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum
import os


class ConsolidationStrategy(Enum):
    """How to consolidate multiple files into one"""
    MERGE_WITH_SECTIONS = "merge_with_sections"  # Create sections with comments
    MERGE_EXPORTS = "merge_exports"  # Combine exports
    KEEP_SEPARATE = "keep_separate"  # Don't consolidate
    GROUP_BY_RESOURCE = "group_by_resource"  # Group by domain entity


@dataclass
class FilePattern:
    """Pattern for matching files"""
    glob: str
    exclude: Optional[List[str]] = None


@dataclass
class TransformRule:
    """Rule for transforming files from standard to CFA structure"""
    name: str
    description: str
    from_patterns: List[FilePattern]
    to_path: str  # Can use {resource}, {feature} placeholders
    strategy: ConsolidationStrategy
    priority: int = 0  # Higher priority runs first
    frameworks: Optional[List[str]] = None  # Which frameworks this rule applies to


@dataclass
class ProjectStructure:
    """Detected project structure information"""
    framework: str  # nextjs, vite, react, remix, etc.
    source_dirs: Set[str]  # src/, app/, pages/, etc.
    has_typescript: bool
    has_app_router: bool  # Next.js App Router
    has_pages_router: bool  # Next.js Pages Router
    components_dir: Optional[str]  # Where components live
    api_dir: Optional[str]  # Where API routes live
    types_dir: Optional[str]  # Where types live
    utils_dir: Optional[str]  # Where utils live


# ============================================================================
# PROJECT STRUCTURE DETECTION
# ============================================================================

def detect_project_structure(project_path: str) -> ProjectStructure:
    """
    Auto-detect project structure and framework

    Returns:
        ProjectStructure with detected information
    """
    source_dirs = set()
    framework = "unknown"
    has_typescript = False
    has_app_router = False
    has_pages_router = False
    components_dir = None
    api_dir = None
    types_dir = None
    utils_dir = None

    # Detect TypeScript
    if os.path.exists(os.path.join(project_path, "tsconfig.json")):
        has_typescript = True

    # Detect source directories
    possible_dirs = ["src", "app", "pages", "lib", "components"]
    for dir_name in possible_dirs:
        dir_path = os.path.join(project_path, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            source_dirs.add(dir_name)

    # Detect framework by package.json dependencies
    package_json_path = os.path.join(project_path, "package.json")
    if os.path.exists(package_json_path):
        import json
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
            deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}

            if "next" in deps:
                framework = "nextjs"
                # Detect App Router vs Pages Router
                if "app" in source_dirs:
                    has_app_router = True
                if "pages" in source_dirs:
                    has_pages_router = True
            elif "vite" in deps:
                framework = "vite"
            elif "@remix-run/react" in deps:
                framework = "remix"
            elif "react" in deps and "vite" not in deps and "next" not in deps:
                framework = "react"

    # Detect component directory
    if "src" in source_dirs:
        # Vite/React style: src/components
        if os.path.exists(os.path.join(project_path, "src", "components")):
            components_dir = "src/components"
    elif "app" in source_dirs:
        # Next.js App Router: app/components
        if os.path.exists(os.path.join(project_path, "app", "components")):
            components_dir = "app/components"
    elif "components" in source_dirs:
        # Root level components
        components_dir = "components"

    # Detect API directory
    if "src" in source_dirs and os.path.exists(os.path.join(project_path, "src", "api")):
        api_dir = "src/api"
    elif "app" in source_dirs and os.path.exists(os.path.join(project_path, "app", "api")):
        api_dir = "app/api"
    elif "pages" in source_dirs and os.path.exists(os.path.join(project_path, "pages", "api")):
        api_dir = "pages/api"

    # Detect types directory
    if "src" in source_dirs and os.path.exists(os.path.join(project_path, "src", "types")):
        types_dir = "src/types"
    elif os.path.exists(os.path.join(project_path, "types")):
        types_dir = "types"

    # Detect utils directory
    if "src" in source_dirs and os.path.exists(os.path.join(project_path, "src", "utils")):
        utils_dir = "src/utils"
    elif "src" in source_dirs and os.path.exists(os.path.join(project_path, "src", "lib")):
        utils_dir = "src/lib"
    elif os.path.exists(os.path.join(project_path, "lib")):
        utils_dir = "lib"

    return ProjectStructure(
        framework=framework,
        source_dirs=source_dirs,
        has_typescript=has_typescript,
        has_app_router=has_app_router,
        has_pages_router=has_pages_router,
        components_dir=components_dir,
        api_dir=api_dir,
        types_dir=types_dir,
        utils_dir=utils_dir,
    )


# ============================================================================
# ADAPTIVE TRANSFORMATION RULES
# ============================================================================

def get_transformation_rules(structure: ProjectStructure) -> List[TransformRule]:
    """
    Generate transformation rules based on detected project structure

    Args:
        structure: Detected project structure

    Returns:
        List of transformation rules adapted to the project
    """
    rules = []

    # Determine base patterns based on structure
    # For src/: use src/**
    # For app/: use app/**
    # For root components/: use components/**
    base_patterns = []
    if "src" in structure.source_dirs:
        base_patterns.append("src")
    if "app" in structure.source_dirs:
        base_patterns.append("app")
    if "components" in structure.source_dirs:
        base_patterns.append("components")
    if not base_patterns:
        base_patterns = ["**"]  # Fallback

    # ========================================================================
    # PRIORITY 1: Types (Must happen first - others depend on this)
    # ========================================================================

    type_patterns = [
        FilePattern("**/*.types.ts"),
        FilePattern("**/types.ts"),
    ]

    if structure.types_dir:
        type_patterns.append(FilePattern(f"{structure.types_dir}/**/*.ts"))
    else:
        # Add flexible patterns
        type_patterns.extend([
            FilePattern("types/**/*.ts"),
            FilePattern("src/types/**/*.ts"),
            FilePattern("app/types/**/*.ts"),
        ])

    rules.append(TransformRule(
        name="Consolidate All Types",
        description="Move all .types.ts, type definitions to shared/types.ts",
        from_patterns=type_patterns,
        to_path="shared/types.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=100,
    ))

    # ========================================================================
    # PRIORITY 2: Shared Utilities
    # ========================================================================

    utils_patterns = []
    if structure.utils_dir:
        utils_patterns.append(FilePattern(f"{structure.utils_dir}/**/*.ts"))
    else:
        # Flexible patterns for common locations
        utils_patterns.extend([
            FilePattern("lib/utils.ts"),
            FilePattern("lib/utils/**/*.ts"),
            FilePattern("utils/**/*.ts"),
            FilePattern("src/lib/**/*.ts"),
            FilePattern("src/utils/**/*.ts"),
        ])

    rules.append(TransformRule(
        name="Consolidate Utils",
        description="Move utils/lib to shared/utils.ts",
        from_patterns=utils_patterns,
        to_path="shared/utils.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=90,
    ))

    TransformRule(
        name="Consolidate Errors",
        description="Move error definitions to shared/errors.ts",
        from_patterns=[
            FilePattern("lib/errors.ts"),
            FilePattern("**/errors.ts"),
            FilePattern("**/*-error.ts"),
        ],
        to_path="shared/errors.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=90,
    ),

    TransformRule(
        name="Database Client",
        description="Move database connection to shared/db-client.ts",
        from_patterns=[
            FilePattern("lib/db.ts"),
            FilePattern("lib/database.ts"),
            FilePattern("lib/prisma.ts"),
        ],
        to_path="shared/db-client.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=90,
    ),

    TransformRule(
        name="Consolidate UI Components",
        description="Move ui/ components (Button, Input, etc.) to shared/ui-components.tsx",
        from_patterns=[
            FilePattern("app/components/ui/**/*.tsx"),
            FilePattern("components/ui/**/*.tsx"),
        ],
        to_path="shared/ui-components.tsx",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=80,
    ),

    # ========================================================================
    # PRIORITY 3: Feature-Specific Components
    # ========================================================================

    TransformRule(
        name="Consolidate Auth Components",
        description="Consolidate LoginForm, SignupForm, etc. → impl/auth-components.tsx",
        from_patterns=[
            FilePattern("app/components/**/Login*.tsx"),
            FilePattern("app/components/**/Signup*.tsx"),
            FilePattern("app/components/**/Auth*.tsx"),
            FilePattern("app/components/**/ForgotPassword*.tsx"),
            FilePattern("components/**/Login*.tsx"),
            FilePattern("components/**/Signup*.tsx"),
        ],
        to_path="impl/auth-components.tsx",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate User Components",
        description="Consolidate UserList, UserCard, etc. → impl/user-components.tsx",
        from_patterns=[
            FilePattern("app/components/**/User*.tsx"),
            FilePattern("components/**/User*.tsx"),
        ],
        to_path="impl/user-components.tsx",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate Other Components by Feature",
        description="Group remaining components by feature (detected from name)",
        from_patterns=[
            FilePattern("app/components/**/*.tsx", exclude=["ui/**"]),
            FilePattern("components/**/*.tsx", exclude=["ui/**"]),
        ],
        to_path="impl/{feature}-components.tsx",
        strategy=ConsolidationStrategy.GROUP_BY_RESOURCE,
        priority=60,
    ),

    # ========================================================================
    # PRIORITY 4: API Routes
    # ========================================================================

    TransformRule(
        name="Consolidate Auth API Routes",
        description="Flatten app/api/auth/** → impl/auth-api.ts",
        from_patterns=[
            FilePattern("app/api/auth/**/route.ts"),
            FilePattern("app/api/login/**/route.ts"),
            FilePattern("app/api/signup/**/route.ts"),
        ],
        to_path="impl/auth-api.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate User API Routes",
        description="Flatten app/api/users/** → impl/user-api.ts",
        from_patterns=[
            FilePattern("app/api/users/**/route.ts"),
        ],
        to_path="impl/user-api.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate Other API Routes by Resource",
        description="Group API routes by resource (detected from path)",
        from_patterns=[
            FilePattern("app/api/**/route.ts"),
        ],
        to_path="impl/{resource}-api.ts",
        strategy=ConsolidationStrategy.GROUP_BY_RESOURCE,
        priority=60,
    ),

    # ========================================================================
    # PRIORITY 5: Server Actions
    # ========================================================================

    TransformRule(
        name="Consolidate Auth Actions",
        description="Move auth server actions → impl/auth-actions.ts",
        from_patterns=[
            FilePattern("app/actions/auth.ts"),
            FilePattern("actions/auth.ts"),
            FilePattern("app/actions/login.ts"),
            FilePattern("app/actions/signup.ts"),
        ],
        to_path="impl/auth-actions.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate User Actions",
        description="Move user server actions → impl/user-actions.ts",
        from_patterns=[
            FilePattern("app/actions/users.ts"),
            FilePattern("actions/users.ts"),
        ],
        to_path="impl/user-actions.ts",
        strategy=ConsolidationStrategy.MERGE_WITH_SECTIONS,
        priority=70,
    ),

    TransformRule(
        name="Consolidate Other Actions by Resource",
        description="Group actions by resource",
        from_patterns=[
            FilePattern("app/actions/**/*.ts"),
            FilePattern("actions/**/*.ts"),
        ],
        to_path="impl/{resource}-actions.ts",
        strategy=ConsolidationStrategy.GROUP_BY_RESOURCE,
        priority=60,
    ),
]


# ============================================================================
# DETECTION PATTERNS
# ============================================================================

# Map component names to features
COMPONENT_FEATURE_MAP = {
    "Login": "auth",
    "Signup": "auth",
    "Auth": "auth",
    "ForgotPassword": "auth",
    "ResetPassword": "auth",
    "User": "user",
    "Profile": "user",
    "Account": "user",
    "Dashboard": "dashboard",
    "Settings": "settings",
    "Invoice": "invoice",
    "Payment": "payment",
    "Product": "product",
    "Cart": "cart",
    "Checkout": "checkout",
}

# Map API paths to resources
API_RESOURCE_MAP = {
    "auth": "auth",
    "login": "auth",
    "signup": "auth",
    "users": "user",
    "profile": "user",
    "posts": "post",
    "comments": "comment",
    "invoices": "invoice",
    "payments": "payment",
    "products": "product",
}


# ============================================================================
# FILES TO PRESERVE (Don't transform these)
# ============================================================================

PRESERVE_FILES = [
    "app/page.tsx",           # Root page
    "app/layout.tsx",         # Root layout
    "app/globals.css",        # Global styles
    "app/**/page.tsx",        # All page files (routing)
    "app/**/layout.tsx",      # All layout files
    "app/**/loading.tsx",     # Loading states
    "app/**/error.tsx",       # Error boundaries
    "app/**/not-found.tsx",   # 404 pages
    "middleware.ts",          # Next.js middleware
    "next.config.ts",         # Next.js config
    "tailwind.config.ts",     # Tailwind config
    "postcss.config.js",      # PostCSS config
    "tsconfig.json",          # TypeScript config
    "package.json",           # Package manifest
    ".env*",                  # Environment files
    "public/**/*",            # Public assets
]


# ============================================================================
# CONSOLIDATION TEMPLATES
# ============================================================================

CONSOLIDATION_TEMPLATES = {
    "components": """// {filename}
// Consolidated components for {feature} feature
// Generated by CFA transformation

import React from 'react';

// ============================================================================
// TYPES
// ============================================================================

// Types are in shared/types.ts - import them there

// ============================================================================
// {section_1_name}
// ============================================================================

{section_1_content}

// ============================================================================
// {section_2_name}
// ============================================================================

{section_2_content}

// ============================================================================
// EXPORTS
// ============================================================================

export {{ {exports} }};
""",

    "api": """// {filename}
// API routes for {feature} resource
// Generated by CFA transformation

import {{ NextRequest, NextResponse }} from 'next/server';

// ============================================================================
// TYPES
// ============================================================================

// Import types from shared/types.ts

// ============================================================================
// GET - List/Retrieve
// ============================================================================

{get_handlers}

// ============================================================================
// POST - Create
// ============================================================================

{post_handlers}

// ============================================================================
// PUT/PATCH - Update
// ============================================================================

{put_handlers}

// ============================================================================
// DELETE - Remove
// ============================================================================

{delete_handlers}
""",

    "actions": """// {filename}
// Server actions for {feature}
// Generated by CFA transformation

'use server';

import {{ revalidatePath }} from 'next/cache';

// ============================================================================
// TYPES
// ============================================================================

// Import types from shared/types.ts

// ============================================================================
// CREATE ACTIONS
// ============================================================================

{create_actions}

// ============================================================================
// UPDATE ACTIONS
// ============================================================================

{update_actions}

// ============================================================================
// DELETE ACTIONS
// ============================================================================

{delete_actions}

// ============================================================================
// QUERY ACTIONS
// ============================================================================

{query_actions}
""",

    "types": """// shared/types.ts
// All TypeScript type definitions
// Generated by CFA transformation

// ============================================================================
// {section_1_name}
// ============================================================================

{section_1_types}

// ============================================================================
// {section_2_name}
// ============================================================================

{section_2_types}
""",
}


def get_feature_from_filename(filename: str) -> str:
    """
    Extract feature name from filename

    Examples:
        LoginForm.tsx → auth
        UserCard.tsx → user
        ProductList.tsx → product
    """
    for pattern, feature in COMPONENT_FEATURE_MAP.items():
        if pattern.lower() in filename.lower():
            return feature

    # Default: use first word before uppercase letter
    # e.g., ProductCard → product
    import re
    match = re.match(r'([A-Z][a-z]+)', filename)
    if match:
        return match.group(1).lower()

    return "misc"


def get_resource_from_api_path(path: str) -> str:
    """
    Extract resource name from API path

    Examples:
        app/api/users/route.ts → user
        app/api/auth/login/route.ts → auth
    """
    parts = path.split('/')

    # Find the part after 'api'
    try:
        api_index = parts.index('api')
        if api_index + 1 < len(parts):
            resource_path = parts[api_index + 1]
            return API_RESOURCE_MAP.get(resource_path, resource_path.rstrip('s'))
    except ValueError:
        pass

    return "misc"
