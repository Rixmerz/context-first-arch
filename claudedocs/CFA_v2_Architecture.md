# Context-First Architecture v2.0

**Status**: ✅ Implemented
**Date**: 2025-12-14
**Migration**: Backwards compatible with CFA v1.0

## Overview

CFA v2.0 is a modernized architecture standard designed **by LLMs, for LLMs**, optimized for context loading and framework compatibility. It maintains the core CFA principles while adapting to modern development tooling (Vite, Next.js, React, etc.).

## Core Invariants

These directories **MUST** exist at the project root in all CFA projects:

```
project/
├── .claude/                 # LLM context layer (INVARIANT)
│   ├── map.md
│   ├── decisions.md
│   ├── current-task.md
│   ├── settings.json        # v2 configuration
│   └── memory.db            # Persistent learnings
└── contracts/               # Feature contracts (INVARIANT)
    └── {feature}.contract.md
```

## v2 Structure (Recommended)

CFA v2 places all source code under a configurable `source_root` (default: `src/`):

```
project/
├── .claude/                 # Context layer
├── contracts/               # Contracts
├── src/                     # Source root (configurable)
│   ├── impl/                # Feature implementations (MANDATORY)
│   │   └── {feature}/       # One directory per contract
│   ├── shared/              # Cross-feature code
│   │   ├── types.ts
│   │   ├── errors.ts
│   │   └── utils.ts
│   ├── app/                 # Application layer (OPTIONAL)
│   │   └── pages/           # Routes, pages, main entry
│   └── infra/               # Infrastructure (OPTIONAL)
│       └── database/
├── tests/                   # Integration/E2E tests (OPTIONAL)
└── package.json
```

### Key Paths

| Path | Purpose | Required |
|------|---------|----------|
| `.claude/` | LLM context and configuration | ✅ Yes |
| `contracts/` | Feature contracts | ✅ Yes |
| `src/impl/` | Feature implementations | ✅ Yes |
| `src/shared/` | Shared utilities, types, errors | ✅ Yes |
| `src/app/` | Application layer (routes, pages) | ⚪ Optional |
| `src/infra/` | Infrastructure (DB, external services) | ⚪ Optional |

## v1 Structure (Legacy)

CFA v1 places `impl/` and `shared/` at the project root:

```
project/
├── .claude/
├── contracts/
├── impl/                    # At root (legacy)
│   └── {feature}/
├── shared/                  # At root (legacy)
│   ├── types.ts
│   ├── errors.ts
│   └── utils.ts
└── package.json
```

**v1 projects continue to work** - all tools automatically detect and support both structures.

## Configuration: `.claude/settings.json`

```json
{
  "cfa_version": "2.0",
  "source_root": "src",
  "framework": "",           // react, next, express, fastapi, etc.
  "project_type": ""         // frontend, backend, fullstack, microservice
}
```

### Configuration Fields

- **cfa_version**: `"2.0"` (new projects) or `"1.0"` (legacy)
- **source_root**: Source directory container (default: `"src"`, v1: `""`)
- **framework**: Optional framework identifier
- **project_type**: Optional project type for documentation

## Framework Adaptability

### Frontend (React/Next.js/Vite)

```
project/
├── .claude/
├── contracts/
├── src/
│   ├── impl/                # Feature components
│   │   ├── auth/            # Authentication feature
│   │   ├── dashboard/       # Dashboard feature
│   │   └── checkout/        # Checkout feature
│   ├── shared/              # Design system, hooks, utils
│   └── app/                 # Next.js app/ or pages/
└── vite.config.ts
```

**Compatibility**: Vite, Next.js, Create React App all support `src/` structure natively.

### Backend (Express/FastAPI/NestJS)

```
project/
├── .claude/
├── contracts/
├── src/
│   ├── impl/                # Domain features
│   │   ├── users/           # User domain
│   │   ├── orders/          # Order domain
│   │   └── payments/        # Payment domain
│   ├── shared/              # DTOs, middleware, validators
│   ├── app/                 # Controllers, routes
│   └── infra/               # Database, external APIs
└── package.json
```

### Microservices

**Each service** is an independent CFA v2 project:

```
services/
├── user-service/
│   ├── .claude/             # Service-specific context
│   ├── contracts/           # Service contracts (API specs)
│   └── src/impl/            # Service implementation
├── order-service/
│   ├── .claude/
│   ├── contracts/
│   └── src/impl/
└── shared/                  # Cross-service types, proto files
```

**Rule**: Each deployable unit = 1 CFA v2 project.

### Monorepo

```
project/
├── .claude/                 # Root context (shared)
├── contracts/               # Shared contracts
├── packages/
│   ├── web/
│   │   ├── .claude/
│   │   ├── contracts/
│   │   └── src/impl/
│   └── api/
│       ├── .claude/
│       ├── contracts/
│       └── src/impl/
└── package.json
```

## Creating Projects

### Create v2 Project (Recommended)

```python
await project_init(
    project_path="/projects/my-app",
    name="My App",
    description="A modern web application",
    languages=["typescript"],
    cfa_version="2.0",        # v2 (default)
    source_root="src"         # default
)
```

Creates:
```
my-app/
├── .claude/
│   ├── map.md
│   ├── decisions.md
│   ├── current-task.md
│   ├── config.json
│   └── settings.json        # ← CFA v2 configuration
├── contracts/
└── src/                     # ← Source root
    ├── impl/
    └── shared/
```

### Create v1 Project (Legacy)

```python
await project_init(
    project_path="/projects/legacy-app",
    name="Legacy App",
    cfa_version="1.0"         # v1 explicitly
)
```

Creates:
```
legacy-app/
├── .claude/
├── contracts/
├── impl/                    # ← At root
└── shared/                  # ← At root
```

## Migration from v1 to v2

CFA projects can be **upgraded in-place**:

### Step 1: Create src/ structure

```bash
mkdir -p src
mv impl src/
mv shared src/
```

### Step 2: Create settings.json

```bash
cat > .claude/settings.json <<EOF
{
  "cfa_version": "2.0",
  "source_root": "src",
  "framework": "",
  "project_type": ""
}
EOF
```

### Step 3: Update config.json

```json
{
  "name": "My Project",
  "cfa_version": "2.0",     // ← Change from "1.0"
  ...
}
```

### Step 4: Update imports

Update any hardcoded `impl/` paths in imports:
- `from impl/user` → `from src/impl/user`
- `import { User } from 'impl/user'` → `import { User } from 'src/impl/user'`

**Note**: Most build tools (TypeScript, Vite) support path aliases to avoid this.

## Tool Compatibility

All MCP tools **automatically detect** project structure:

```python
from core.project import get_project_paths

# Works for both v1 and v2
paths = get_project_paths("/path/to/project")

impl_dir = paths["impl_dir"]       # → path/impl OR path/src/impl
shared_dir = paths["shared_dir"]   # → path/shared OR path/src/shared
contracts_dir = paths["contracts_dir"]
claude_dir = paths["claude_dir"]
```

Tools that auto-detect structure:
- ✅ `project.init` - Creates v1 or v2 based on parameters
- ✅ `project.scan` - Scans correct impl/ location
- ✅ `contract.*` - Finds impl files in correct location
- ✅ `dependency.*` - Analyzes dependencies in correct structure
- ✅ `map.auto_update` - Updates based on correct paths
- ✅ All 23 MCP tools

## Design Principles

### 1. LLM-First Design

CFA v2 maintains **predictable paths** for efficient context loading:

```python
# LLM can always load context with O(1) lookups:
project_map = read_file(".claude/map.md")
settings = read_file(".claude/settings.json")
impl_dir = Path(settings["source_root"]) / "impl"
```

### 2. Feature-Centric Organization

Features remain the **atomic unit of organization**:

```
src/impl/user/           # One feature
├── user.service.ts      # Core logic
├── user.types.ts        # Feature types
├── user.test.ts         # Feature tests
└── __tests__/           # Integration tests
```

**Not** organized by file type:
```
❌ src/services/user.service.ts
❌ src/types/user.types.ts
❌ src/tests/user.test.ts
```

### 3. Framework Agnostic

CFA v2 adapts to **any framework**:

- ✅ React/Vue/Svelte - `src/impl/` holds components
- ✅ Express/Fastify/NestJS - `src/impl/` holds domains
- ✅ Next.js - `src/impl/` for features, `src/app/` for routes
- ✅ Microservices - Each service is a CFA project

### 4. Backwards Compatible

**All v1 projects continue to work** without modification.

## FAQ

### Why `src/impl/` instead of `impl/` at root?

**Modern tooling compatibility**. Vite, TypeScript, Jest all expect source code in `src/`. CFA v2 adapts to ecosystem standards.

### Can I use a different source_root?

Yes! Set `source_root` in `.claude/settings.json`:

```json
{
  "cfa_version": "2.0",
  "source_root": "lib"      // → lib/impl/, lib/shared/
}
```

### Do I need to migrate v1 projects?

**No**. v1 projects work indefinitely. Migrate only if you need framework compatibility.

### What if my framework requires specific structure?

Use optional directories:

```
src/
├── impl/            # CFA features
├── shared/          # CFA shared code
├── app/             # Next.js app router
├── pages/           # Next.js pages router
├── public/          # Static assets
└── styles/          # Global styles
```

CFA only mandates `impl/` and `shared/` - everything else is flexible.

### How do microservices work?

Each service = independent CFA v2 project:

```
user-service/
├── .claude/         # ← Service context
├── contracts/       # ← Service API contracts
└── src/impl/        # ← Service implementation

order-service/
├── .claude/
├── contracts/
└── src/impl/
```

Optional: Root `.claude/` for cross-service context.

## Implementation Summary

### Files Modified

| File | Changes |
|------|---------|
| `core/project.py` | Added `cfa_version`, `source_root`, `get_project_paths()` |
| `mcp_server/tools/project_init.py` | Added v2 parameters, dual structure support |
| All 13 MCP tools | Use `get_project_paths()` instead of hardcoded `path / "impl"` |
| `core/map_generator.py` | Auto-detect impl/shared locations |
| `core/test_analyzer.py` | Find tests in correct locations |

### Backward Compatibility

✅ **v1 projects work without changes**
✅ **Tools auto-detect structure**
✅ **No forced migration**
✅ **Gradual adoption path**

## Conclusion

CFA v2 modernizes Context-First Architecture while preserving its core philosophy:

- 🎯 **LLM-optimized**: Predictable paths, centralized context
- 🔧 **Framework-compatible**: Works with Vite, Next.js, modern tooling
- 📦 **Feature-centric**: Features remain atomic units
- ♻️ **Backwards compatible**: v1 projects continue working
- 🌍 **Universal**: Frontend, backend, microservices

**Recommendation**: Use CFA v2 for new projects, migrate v1 projects as needed.
