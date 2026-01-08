# Project Map - CFA v4

## What This Project Does

Context-First Architecture (CFA) v4 is a minimalist MCP server that provides 4 tools for AI-assisted development:
- **cfa.onboard** - Load project context
- **cfa.remember** - Store persistent knowledge
- **cfa.recall** - Retrieve stored knowledge  
- **cfa.checkpoint** - Git-based safe points

Philosophy: "Architecture over indexing" - good project structure makes complex indexing unnecessary.

## Entry Points

- `cfa4-server` / `cfa4` - CLI commands to start the MCP server
- `src/cfa_v4/server.py` - Main server module

## Directory Structure

```
src/cfa_v4/
├── __init__.py
├── README.md           # Philosophy doc
├── server.py           # MCP server (entry point)
├── templates/          # Init templates for new projects
│   ├── map.md.template
│   ├── decisions.md.template
│   ├── current-task.md.template
│   └── settings.json.template
└── tools/
    ├── __init__.py
    ├── onboard.py      # cfa.onboard implementation
    ├── memory.py       # cfa.remember & cfa.recall
    └── checkpoint.py   # cfa.checkpoint (git-based)
```

## Key Concepts

1. **No databases** - All storage is JSON/Markdown in `.claude/`
2. **No complex indexing** - Good architecture > sophisticated RAG
3. **Git-native** - Checkpoints are just git commits with `[CFA-SAFE]` prefix
4. **Zero dependencies** - Only requires `mcp` package

## Data Flow

```
[Session Start] → cfa.onboard → reads .claude/*.md
[Learning] → cfa.remember → writes .claude/memories.json
[Retrieval] → cfa.recall → reads .claude/memories.json
[Safe Point] → cfa.checkpoint → git commit/rollback
```

## Non-Obvious Things

- `cfa.onboard` with `init_if_missing=true` bootstraps new projects
- `cfa.checkpoint` requires a git repository
- Memories are stored as flat JSON array, not a database
- All tools are async but storage is synchronous (intentional simplicity)
