# Context-First Architecture (CFA)

A framework designed to optimize LLM interaction with codebases through information density and flat structure.

## Philosophy

**The problem**: LLMs process text sequentially with limited context windows. Every file read consumes tokens. Every search is a round-trip. Fragmentation and ambiguity are the enemy.

**The solution**: Structure projects so an LLM can understand them with 2-3 reads, not 20 searches and 15 fragmented files.

## Project Structure

```
proyecto/
├── .claude/
│   ├── map.md              # THE MOST IMPORTANT FILE - Project navigation
│   ├── decisions.md        # WHY decisions were made (ADRs)
│   └── current-task.md     # Session state for continuity
│
├── contracts/
│   └── *.contract.md       # WHAT modules do, not HOW (Markdown)
│
├── impl/
│   ├── feature.ts          # Complete implementation in ONE file
│   └── feature.test.ts     # Tests alongside implementation
│
└── shared/
    ├── types.ts            # ALL types in one place
    ├── errors.ts           # ALL errors in one place
    └── utils.ts            # Shared utilities
```

## Key Principles

| Principle | Why |
|-----------|-----|
| **Fewer, complete files** | Less reads = more context |
| **Flat structure (max 2 levels)** | Less navigation |
| **Descriptive unique names** | `user-auth.ts` not `service.ts` |
| **Markdown for docs** | Native format for LLMs |
| **Types with implementation** | No hunting in separate files |
| **map.md is mandatory** | Instant project understanding |

## What We Avoid

- `index.ts` that only re-exports (useless indirection)
- 50-line files (extreme fragmentation)
- `utils/`, `helpers/`, `common/` folders (junk drawers)
- Generic names (`handler.ts`, `service.ts`)
- Barrel exports (hide real structure)
- Separate `.d.ts` files (types far from implementation)
- Deep nesting like `src/domain/entities/user/User.ts`

## MCP Tools

| Tool | Purpose |
|------|---------|
| `context.load` | **START HERE** - Load map.md + current-task.md in ONE call |
| `project.init` | Create new CFA project |
| `project.scan` | Update map.md from code analysis |
| `project.migrate` | Convert existing project to CFA |
| `contract.create` | Generate contract from implementation |
| `contract.validate` | Validate impl matches contract |
| `task.start` | Begin a new task |
| `task.update` | Track progress |
| `task.complete` | Mark task done |
| `decision.add` | Document architecture decision |

## Quick Start

### Create New Project

```bash
# Via MCP tool
cfa project.init --path ./my-app --name "My App" --languages typescript

# Creates:
# my-app/
# ├── .claude/
# │   ├── map.md
# │   ├── decisions.md
# │   └── current-task.md
# ├── contracts/
# ├── impl/
# └── shared/
#     ├── types.ts
#     ├── errors.ts
#     └── utils.ts
```

### Migrate Existing Project

```bash
cfa project.migrate --source ./old-project --target ./old-project-cfa
```

### Start Working

```bash
# Always start by loading context
cfa context.load --path ./my-app

# Start a task
cfa task.start --path ./my-app --goal "Implement user authentication"

# Update progress
cfa task.update --path ./my-app --completed "Added login endpoint" --files-modified "impl/auth.ts"

# Complete task
cfa task.complete --path ./my-app --summary "Auth complete with JWT"
```

## Installation

```bash
pip install context-first-architecture

# With tree-sitter for better code analysis
pip install context-first-architecture[tree-sitter]
```

## Configuration for Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "cfa": {
      "command": "cfa-server",
      "args": []
    }
  }
}
```

## License

MIT
