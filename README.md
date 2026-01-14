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

**The solution:** Structure projects so an LLM can understand a feature in ONE read, not by navigating 5 files.

### The Golden Rules

```
1. ONE file per feature (no matter the size)
2. Shared code = ONE place only (utils/)
3. Features NEVER import from other features
4. File length is NOT a reason to split
```

### Architecture

```
src/
├── features/
│   ├── auth/
│   │   ├── auth.ts          # ALL auth logic (100 or 3000 lines)
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

**Why ONE file per feature works for LLMs:**
- **One read = complete context** — No missing dependencies, no surprises
- **Grep is enough** — Need just `validateToken`? → `grep -A 30 "function validateToken"`
- **No import resolution** — Everything is right there
- **Long files are NOT a problem** — I can process 200k tokens; I can grep 3000 lines easily

### Why NOT Split Large Features?

Traditional wisdom says "split files > 300 lines." This optimizes for **human readability**, not **agent efficiency**.

| Scenario | Multiple files | Single file |
|----------|----------------|-------------|
| Read entire feature | 4-5 file reads | 1 file read |
| Find specific function | Open correct file first | `grep -A 30 "function name"` |
| Understand dependencies | Follow imports between files | Already visible |
| Context completeness | Risk missing a file | Guaranteed complete |
| Tokens consumed | High (navigation overhead) | Low (one read) |

**The 300-line rule is human legacy.** For AI-assisted development, consolidation beats fragmentation.

### Internal Structure (for large files)

Use comments/regions for navigation. The file stays unified, but sections are grep-able:

```typescript
// ============================================
// AUTH MODULE
// ============================================

// --- Types ---
interface User { ... }
interface Session { ... }

// --- Token Management ---
function createToken() { ... }
function validateToken() { ... }
function refreshToken() { ... }

// --- Session Management ---
function createSession() { ... }
function destroySession() { ... }

// --- Public API ---
export { createToken, validateToken, createSession, destroySession }
```

An LLM can `grep "// --- Token"` and get exactly that section.

### Decision Tree

```
1. Does multiple features need this code?
   → YES: Move to utils/
   → NO: Keep in the feature file

2. Am I importing from another feature?
   → STOP. Extract shared logic to utils/ instead.

3. Is my feature file getting long?
   → Add section comments. DO NOT split into multiple files.
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

- **Splitting features into multiple files** — Fragments context unnecessarily
- **Importing feature → feature** — Extract to utils/ instead
- **Subdirectories in utils/** (`utils/types/`, `utils/helpers/`) — Keep it flat
- **Subdirectories in features** (`feature/core/`, `feature/api/`) — Over-engineering
- **Deep nesting** (`src/domain/entities/user/User.ts`) — Hard to navigate
- **The "300 line rule"** — Human legacy, not agent-optimal

### Real-World Example: This Project

```
src/cfa_v4/
├── server.py              # Entry point
├── tools/                 # Features (each tool = one file)
│   ├── onboard.py         # ALL onboard logic
│   ├── remember.py        # ALL remember logic
│   ├── recall.py          # ALL recall logic
│   └── checkpoint.py      # ALL checkpoint logic
└── templates/             # Shared resources
    └── *.md
```

**Why this structure:**
- **1 file = 1 feature** — Complete context in one read
- **No cross-imports between tools** — Each tool is self-contained
- **Templates are shared** — Used by multiple tools, extracted to common location

### Testing Strategy

Tests live next to implementation. One test file per feature.

```
feature/
├── feature.ts       # All feature logic
└── feature.test.ts  # All feature tests
```

### Why This Architecture? (Technical Justification)

I evaluated three competing approaches:

**Approach A (Enterprise-style): Many small files**
```
features/auth/core/, api/, models/, tests/
```

**Approach B (Compromise): Split at 300 lines**
```
features/auth/auth.ts, auth-tokens.ts, auth-session.ts
```

**Approach C (Agent-optimal): One file per feature**
```
features/auth/auth.ts, auth.test.ts
```

**Analysis from LLM perspective:**

| Metric | Approach A | Approach B | Approach C |
|--------|------------|------------|------------|
| Files to read per feature | 5-10 | 3-5 | 1 |
| Import resolution needed | Heavy | Medium | None |
| Risk of incomplete context | High | Medium | Zero |
| Grep effectiveness | Low (which file?) | Medium | High (one file) |
| Tokens for navigation | High | Medium | Minimal |

**Analysis from Human perspective:**

| Metric | Approach A | Approach B | Approach C |
|--------|------------|------------|------------|
| File readability | High (small files) | Medium | Lower (long files) |
| Navigation | Complex | Medium | Simple (one file) |
| IDE support | Good | Good | Good (folding, outline) |

**Conclusion:**

Approach C is optimal for AI-assisted development because:

1. **One read = complete context** — No risk of missing dependencies
2. **Grep replaces navigation** — `grep -A 50 "function name"` extracts exactly what's needed
3. **Long files are not a problem for LLMs** — We process 200k tokens; 3000 lines is trivial
4. **Fragmentation is the real enemy** — Every additional file is overhead

The traditional "small files" wisdom optimizes for human cognition (limited working memory, visual scanning). For agents with large context windows and text search capabilities, **consolidation beats fragmentation**.

Humans can still navigate long files effectively using IDE features (folding, outline, search). The structure serves both audiences.

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
