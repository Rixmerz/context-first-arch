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

```bash
# With uv (recommended)
uv pip install context-first-architecture

# Or with pip
pip install context-first-architecture
```

## Usage with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "cfa4": {
      "command": "cfa4-server"
    }
  }
}
```

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
