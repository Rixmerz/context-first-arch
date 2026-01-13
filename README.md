# Context-First Architecture (CFA) v4

> "Architecture over indexing."

A minimalist 4-tool MCP server for AI-assisted development.

## Philosophy

Good project structure makes complex indexing unnecessary. CFA v4 deliberately avoids:
- Knowledge graphs and RAG pipelines
- SQLite databases
- Complex orchestration systems
- 27+ tools that overlap

Instead, it provides **4 tools** that do one thing well.

## The 4 Tools

| Tool | Purpose |
|------|---------|
| `cfa.onboard` | Load project context from `.claude/` directory |
| `cfa.remember` | Store knowledge persistently (JSON-based) |
| `cfa.recall` | Retrieve stored knowledge by key, query, or tags |
| `cfa.checkpoint` | Create/list/rollback git-based safe points |

## Installation

### Option 1: Direct from GitHub with uvx (Recommended)

Add to your Claude Code MCP configuration (`~/.config/claude/mcp_settings.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "cfa4": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Rixmerz/context-first-arch",
        "cfa4-server"
      ]
    }
  }
}
```

**Advantages:**
- No global installation needed
- Always uses latest version from repository
- Isolated environment per execution

### Option 2: Install with pip/uv

```bash
# With uv
uv pip install context-first-architecture

# Or with pip
pip install context-first-architecture
```

Then configure MCP:

```json
{
  "mcpServers": {
    "cfa4": {
      "command": "cfa4-server"
    }
  }
}
```

### Enforcement Hooks (Optional)

Install hooks that **enforce** the CFA protocol:

```bash
cfa4-install          # Install hooks
cfa4-install --remove # Uninstall hooks
```

**What hooks do:**
- Block `Edit`/`Write` until `cfa.onboard()` is called
- Only apply to projects with `.claude/` directory
- Install globally in `~/.claude/hooks/`

**Note:** Restart Claude Code after installing hooks.

## Project Setup

Initialize CFA in any project:

```
cfa.onboard(project_path=".", init_if_missing=true)
```

This creates:
```
.claude/
├── map.md           # Project structure
├── decisions.md     # Architecture decisions (ADRs)
├── current-task.md  # Current task tracking
├── settings.json    # CFA configuration
└── memories.json    # Persistent knowledge store
```

## Project Structure Guidelines

### The Problem CFA Solves

LLMs process text sequentially with limited context windows. Each file read consumes tokens. Each search is a round-trip. Fragmentation and ambiguity are the enemy.

**The solution:** Structure projects so an LLM can understand them in 2-3 reads, not 20 searches and 15 fragmented files.

### Structure by Complexity

**Simple Features (< 100 lines)**
```
src/features/theme-toggle/
├── theme-toggle.ts
└── theme-toggle.test.ts
```

**Medium Features (100-300 lines)**
```
src/features/notifications/
├── notifications.ts
├── notifications-utils.ts
├── notifications.test.ts
└── index.ts
```

**Complex Features (> 300 lines, multiple layers)**
```
src/features/authentication/
├── core/
│   ├── auth-service.ts
│   ├── token-manager.ts
│   └── session-store.ts
├── api/
│   ├── auth-routes.ts
│   └── auth-middleware.ts
├── models/
│   └── user-session.ts
├── tests/
│   ├── unit/
│   └── integration/
└── index.ts
```

### Decision Tree

```
1. Is the feature < 100 total lines?
   → YES: Single file + test file
   → NO: Continue to 2

2. Does the feature have multiple layers? (API + Business + Data)
   → YES: Use subdirectories (core/, api/, models/)
   → NO: Continue to 3

3. Is the feature 100-300 lines?
   → YES: Split into main file + utilities
   → NO: Use complex feature structure with subdirectories

4. Is the code used by multiple features?
   → YES: Move to src/shared/
   → NO: Keep in feature directory
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Features | Noun-based | `notifications.ts`, `auth-service.ts` |
| Utilities | Descriptive | `date-utils.ts`, `validators.ts` |
| Tests | Match source | `auth-service.test.ts` |
| Index files | Always `index.ts` | Public API of the module |

### Anti-patterns to Avoid

- **`index.ts` that only re-exports** — useless indirection
- **50-line files** — extreme fragmentation
- **Generic folders** (`utils/`, `helpers/`, `common/`) — junk drawers
- **Generic names** (`handler.ts`, `service.ts`) — meaningless
- **Deep nesting** (`src/domain/entities/user/User.ts`) — hard to navigate
- **Barrel exports** — hide real structure
- **Separate `.d.ts` files** — types far from implementation

### Real-World Example: This Project

CFA v4 uses a 3-layer architecture:

```
src/cfa_v4/
├── server.py              # Entry point
├── tools/                 # MCP tool layer (public API)
│   ├── onboard.py
│   ├── remember.py
│   ├── recall.py
│   └── checkpoint.py
├── core/                  # Business logic (internal)
│   └── (future extraction)
└── templates/             # Init templates
    └── *.md
```

**Why this structure:**
- **1 file = 1 tool** — easy to find and modify
- **Tools layer is public** — what users interact with
- **Core layer is internal** — business logic extracted from tools
- **Clear boundaries** — public vs internal

### Testing Location Strategy

| Feature Type | Test Location |
|--------------|---------------|
| Simple | Co-located: `feature.test.ts` next to `feature.ts` |
| Medium | Single test file in feature directory |
| Complex | Dedicated `tests/` subdirectory with `unit/` and `integration/` |

## Example Workflow

```python
# 1. Start session - load context
cfa.onboard(project_path=".")

# 2. Store a learning
cfa.remember(
    project_path=".",
    key="api-pattern",
    value="All endpoints use /api/v1 prefix",
    tags=["pattern", "api"]
)

# 3. Before risky changes
cfa.checkpoint(
    project_path=".",
    action="create",
    message="Before refactoring auth module"
)

# 4. If something breaks
cfa.checkpoint(
    project_path=".",
    action="rollback",
    checkpoint_id="abc123"
)

# 5. Recall past knowledge
cfa.recall(project_path=".", query="api")
```

## Why v4?

Previous versions (v1-v3) grew to 27+ tools with:
- Knowledge graph with chunking and compression
- SQLite databases for memory, orchestration, rules
- Complex LSP integration
- Business rules engine

**v4 strips it down to essentials.** The complexity wasn't providing proportional value.

## Requirements

- Python 3.10+
- Git (for checkpoints)
- MCP-compatible client (Claude Code, etc.)

## License

MIT
