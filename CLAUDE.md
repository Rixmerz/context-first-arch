# CLAUDE.md - CFA v4 Project Instructions

This project uses **Context-First Architecture (CFA) v4** - a minimalist 4-tool framework.

## Philosophy

> "Architecture over indexing."

Good project structure makes complex indexing unnecessary. CFA v4 provides:
- 4 simple tools (not 27+)
- JSON/Markdown storage (no databases)
- Git-based checkpoints (no complex orchestration)

## Session Start Protocol

At the START of every session:
```
cfa.onboard(project_path=".")
```

This loads:
- `.claude/map.md` - Project structure
- `.claude/decisions.md` - Architecture decisions
- `.claude/current-task.md` - Current task state
- `.claude/memories.json` - Persistent knowledge

## The 4 Tools

### 1. cfa.onboard
Load project context in one call. Use `init_if_missing=true` to bootstrap new projects.

### 2. cfa.remember
Store knowledge persistently:
```
cfa.remember(key="auth-pattern", value="Uses JWT with refresh tokens", tags=["pattern"])
```

### 3. cfa.recall
Retrieve stored knowledge:
```
cfa.recall(query="authentication")  # Search by text
cfa.recall(tags=["gotcha"])         # Search by tags
cfa.recall(key="auth-pattern")      # Exact key lookup
```

### 4. cfa.checkpoint
Git-based safe points:
```
cfa.checkpoint(action="create", message="Before refactoring auth")
cfa.checkpoint(action="list")
cfa.checkpoint(action="rollback", checkpoint_id="abc123", dry_run=true)
```

## Project Structure

```
context-first-arch/
├── src/cfa_v4/           # The CFA v4 server
│   ├── server.py         # MCP server entry point
│   ├── tools/            # The 4 tools
│   └── templates/        # Init templates
├── .claude/              # Project metadata
│   ├── map.md
│   ├── decisions.md
│   ├── current-task.md
│   ├── settings.json
│   └── memories.json
└── pyproject.toml
```

## When to Use Each Tool

| Situation | Tool |
|-----------|------|
| Starting a session | `cfa.onboard` |
| Learned something important | `cfa.remember` |
| Need past knowledge | `cfa.recall` |
| Before risky changes | `cfa.checkpoint(action="create")` |
| Something broke | `cfa.checkpoint(action="rollback")` |
