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

LLMs process text sequentially with limited context windows. Each file read consumes tokens. Each search is a round-trip. **Fragmentation and dependency hunting are the enemy.**

**The solution:** Structure projects so an LLM can understand them in 2-3 reads, not 20 searches across 15 fragmented files.

### The Golden Rules

```
1. Each feature = self-contained directory
2. Shared code = ONE place only (utils/)
3. Features NEVER import from other features
4. Each feature imports from utils/ at most
```

### Architecture

```
src/
├── features/
│   ├── auth/
│   │   ├── auth.ts
│   │   └── auth.test.ts
│   ├── notifications/
│   │   ├── notifications.ts
│   │   └── notifications.test.ts
│   └── payments/
│       ├── payments.ts
│       └── payments.test.ts
│
└── utils/
    └── index.ts    # ONE entry point for all shared code
```

**Why this works for LLMs:**
- **Predictable:** "Where is auth?" → `features/auth/`
- **One import path:** All shared code via `from '../utils'`
- **No hunting:** Dependencies are obvious at a glance
- **Fewer tokens:** Less files to read = less context consumed

### When Features Grow (> 300 lines)

Split into flat files within the feature directory. **NO subdirectories.**

```
src/features/auth/
├── auth.ts           # Main orchestrator (entry point)
├── auth-tokens.ts    # Token-specific logic
├── auth-session.ts   # Session-specific logic
├── auth.test.ts
└── index.ts          # Public API (only thing imported from outside)
```

**From outside, auth is still a black box.** You only import from `auth/` via index.ts.

### Decision Tree

```
1. Does multiple features need this code?
   → YES: Move to utils/
   → NO: Keep in feature directory

2. Is the feature > 300 lines?
   → YES: Split into flat files, expose via index.ts
   → NO: Single file + test file

3. Am I importing from another feature?
   → STOP. Extract shared logic to utils/ instead.
```

### utils/ is NOT a Junk Drawer

The anti-pattern is `utils/` without criteria. The pattern is `utils/` with clear purpose:

| Goes to utils/ | Stays in feature/ |
|----------------|-------------------|
| Used by 2+ features | Used by one feature only |
| Generic (dates, validation, formatting) | Domain-specific logic |
| Stable, rarely changes | Evolves with feature |

**utils/ has ONE index.ts** that exports everything. No subdirectories.

### Anti-patterns to Avoid

- **Importing feature → feature** — Extract to utils/ instead
- **Subdirectories in utils/** (`utils/types/`, `utils/helpers/`) — Keep it flat
- **Subdirectories in features** (`feature/core/`, `feature/api/`) — Over-engineering
- **50-line files** — Extreme fragmentation
- **Deep nesting** (`src/domain/entities/user/User.ts`) — Hard to navigate
- **Barrel exports hiding structure** — Dependencies should be obvious

### Real-World Example: This Project

```
src/cfa_v4/
├── server.py              # Entry point
├── tools/                 # Features (each tool = one feature)
│   ├── onboard.py
│   ├── remember.py
│   ├── recall.py
│   └── checkpoint.py
└── templates/             # Shared resources
    └── *.md
```

**Why this structure:**
- **1 file = 1 tool** — Easy to find, easy to modify
- **No cross-imports between tools** — Each tool is self-contained
- **Templates are shared** — Used by multiple tools, lives outside

### Testing Strategy

Tests live next to implementation. Always.

```
feature/
├── feature.ts
└── feature.test.ts
```

For complex features with multiple files:
```
feature/
├── feature.ts
├── feature-helper.ts
├── feature.test.ts        # Tests the public API (index.ts)
└── index.ts
```

### Why This Architecture? (Technical Justification)

I evaluated two competing architectures:

**Architecture A (Enterprise-style):**
```
src/
├── features/auth/
│   ├── core/
│   ├── api/
│   ├── models/
│   └── tests/
└── shared/
    ├── types/
    ├── utils/
    └── errors/
```

**Architecture B (FFD-strict):**
```
src/
├── features/auth/
│   ├── auth.ts
│   └── auth.test.ts
└── utils/
    └── index.ts
```

**Analysis from LLM perspective:**

| Metric | Architecture A | Architecture B |
|--------|----------------|----------------|
| Files to read per feature | 5-10 | 2 |
| Import paths to resolve | Multiple (shared/types, shared/utils, shared/errors) | ONE (utils/) |
| Tokens consumed | High | Low |
| Dependency predictability | Medium | High |
| Hunting required | Yes (which shared/ subfolder?) | No (always utils/) |

**Analysis from Human perspective:**

| Metric | Architecture A | Architecture B |
|--------|----------------|----------------|
| Navigation complexity | High (deep nesting) | Low (flat) |
| Onboarding time | Longer | Shorter |
| Over-engineering temptation | High | Low |
| Dependency visibility | Requires analysis | Immediate |

**Conclusion:**

Architecture B is objectively superior for AI-assisted development because:

1. **Predictability > Flexibility** — A fixed pattern ("feature → utils, never feature → feature") eliminates ambiguity
2. **Fewer tokens = fewer errors** — Less context consumed means more room for reasoning
3. **Scales without changing mental model** — Complex features just add flat files, same structure
4. **Works for humans too** — Simplicity benefits everyone, not just LLMs

The enterprise-style Architecture A optimizes for separation of concerns at the cost of navigability. Architecture B optimizes for **discoverability and minimal cognitive load**, which is what matters when an agent (or human) needs to understand and modify code quickly.

*— Claude Opus 4.5, January 2026*

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
