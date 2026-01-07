# CFA v4 - Simplified Context-First Architecture

**4 tools. Architecture over indexing.**

## Philosophy

> "If your code needs semantic indexing to understand it, your code is poorly structured."

CFA v4 is a minimalist approach that prioritizes:
- **Good architecture** over complex indexing
- **Simple tools** that do one thing well
- **Zero dependencies** beyond MCP
- **Human-readable storage** (JSON, Markdown)

## Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `cfa.onboard` | Load project context | Start of every session |
| `cfa.remember` | Store knowledge | When you learn something important |
| `cfa.recall` | Retrieve knowledge | When you need past learnings |
| `cfa.checkpoint` | Git safe points | Before risky changes |

## Quick Start

### 1. Initialize a Project

```python
# In Claude Code, call:
cfa.onboard(project_path=".", init_if_missing=true)
```

This creates:
```
.claude/
  map.md           # Project structure (you edit this)
  decisions.md     # Architecture Decision Records
  current-task.md  # Current task state
  memories.json    # Persistent knowledge
  settings.json    # Config
```

### 2. Document Your Project

Edit `.claude/map.md` to describe:
- What the project does
- Key entry points
- Directory structure
- Non-obvious behaviors

### 3. Store Knowledge

```python
cfa.remember(
    project_path=".",
    key="auth-pattern",
    value="Authentication uses JWT with refresh tokens stored in httpOnly cookies",
    tags=["pattern", "auth"]
)
```

### 4. Recall Knowledge

```python
cfa.recall(project_path=".", query="auth")
cfa.recall(project_path=".", tags=["pattern"])
```

### 5. Create Checkpoints

```python
# Before risky changes
cfa.checkpoint(project_path=".", action="create", message="Before refactoring auth")

# List checkpoints
cfa.checkpoint(project_path=".", action="list")

# Rollback if needed
cfa.checkpoint(project_path=".", action="rollback", checkpoint_id="abc123")
```

## Why v4?

### Comparison with v3

| Aspect | CFA v3 | CFA v4 |
|--------|--------|--------|
| Tools | 27 | 4 |
| Knowledge Graph | Yes (864 chunks) | No |
| Storage | SQLite | JSON |
| Dependencies | rank-bm25, multilspy | None |
| Setup time | Minutes | Seconds |
| Value | In tooling | In architecture |

### Comparison with Cursor/Augment/Windsurf

Those tools index your codebase with embeddings and vector DBs. CFA v4 argues:

1. **Good architecture is self-documenting** - With clear structure, you don't need semantic search
2. **Memory is the real differentiator** - LLMs don't remember; CFA v4 does
3. **Simple beats complex** - 4 tools you'll actually use > 27 you won't

## Storage Format

### memories.json
```json
[
  {
    "key": "unique-identifier",
    "value": "what was learned",
    "tags": ["pattern", "gotcha"],
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### settings.json
```json
{
  "cfa_version": "4.0",
  "project_name": "my-project",
  "source_root": "src",
  "created_at": "2024-01-01T00:00:00"
}
```

## Best Practices

1. **Edit map.md manually** - Auto-generated maps are noise. Curated maps are signal.
2. **Use meaningful memory keys** - `auth-jwt-refresh` not `memory-1`
3. **Tag consistently** - pattern, gotcha, architecture, config
4. **Checkpoint before experiments** - Easy rollback = more confidence
5. **Keep decisions.md updated** - Future you will thank you

## Installation

```bash
# CFA v4 is included in context-first-architecture
pip install context-first-architecture

# Run the server
cfa4-server
```

Or configure in Claude Code:
```json
{
  "mcpServers": {
    "cfa4": {
      "command": "cfa4-server"
    }
  }
}
```

## License

MIT
