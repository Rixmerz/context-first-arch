# Context-First Architecture + Serena MCP Server

## Purpose
Unified MCP server providing **51 tools** for AI-assisted development combining:
- **CFA v2**: Architecture optimized for LLM context (contracts, features, dependencies)
- **Serena**: Semantic code analysis via LSP (symbols, references, refactoring)

## Entry Points
- `src/mcp_server/server.py:main()` → MCP server (51 tools)
- `cfa` / `cfa-server` → CLI commands

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CFA + Serena MCP Server                      │
├─────────────────────────────────────────────────────────────────┤
│  src/core/           │  src/mcp_server/                         │
│  ├── project.py      │  ├── server.py (51 tools registered)     │
│  ├── analyzers/      │  └── tools/                              │
│  ├── lsp/            │      ├── project_*.py (3)                │
│  │   ├── manager.py  │      ├── contract_*.py (4)               │
│  │   └── symbols.py  │      ├── task_*.py (3)                   │
│  ├── workflow/       │      ├── memory_*.py (6)                 │
│  │   ├── onboarding  │      ├── symbol_*.py (7) + lsp_*.py (2)  │
│  │   └── reflection  │      ├── file_*.py (9)                   │
│  └── memory_store.py │      └── workflow_*.py (7)               │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Tools (51 total)

### CFA Core Tools (20)

**Project Management (3)**
- `project.init` - Create CFA v2 project
- `project.scan` - Scan and update map.md
- `project.migrate` - Convert existing project

**Contract Management (4)**
- `contract.create` - Generate from implementation
- `contract.validate` - Validate against implementation
- `contract.diff` - Compare contract vs code
- `contract.sync` - Sync from code changes

**Task Management (3)**
- `task.start` - Begin new task
- `task.update` - Update progress
- `task.complete` - Mark complete

**Decision & Context (3)**
- `decision.add` - Document architecture decisions
- `context.load` - Load project context
- `context.optimize` - Optimize for token limits

**Analysis (4)**
- `dependency.analyze` - Analyze dependencies
- `pattern.detect` - Detect code patterns
- `impact.analyze` - Calculate change impact
- `coupling.analyze` - Analyze feature coupling

**Documentation (3)**
- `docs.generate` - Generate documentation
- `map.auto_update` - Auto-update map.md
- `test.coverage_map` - Map test coverage

### Memory Tools (6)
- `memory.set` - Store learning
- `memory.get` - Retrieve by key
- `memory.search` - Search by query/tags
- `memory.list` - List all memories
- `memory.edit` - Edit existing memory
- `memory.delete` - Delete memory

### Symbol Tools - Serena (9)
- `symbol.find` - Find symbols by name
- `symbol.overview` - Get file symbol hierarchy
- `symbol.references` - Find all references
- `symbol.replace` - Replace symbol body
- `symbol.insert_after` - Insert after symbol
- `symbol.insert_before` - Insert before symbol
- `symbol.rename` - Rename across project
- `lsp.status` - Get LSP server status
- `lsp.restart` - Restart LSP server(s)

### File Tools - Serena (9)
- `file.read` - Read with line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Search and replace
- `file.delete_lines` - Delete specific lines
- `file.replace_lines` - Replace line range
- `file.insert_at_line` - Insert at line
- `file.search` - Search across files (grep)

### Workflow Tools - Serena (7)
- `workflow.onboard` - Generate project context
- `workflow.check_onboard` - Verify onboarding status
- `workflow.think_info` - Reflect on information
- `workflow.think_task` - Validate approach
- `workflow.think_done` - Verify completion
- `workflow.summarize` - Summarize changes
- `workflow.instructions` - Get CFA workflow guide

## Core Framework

### src/core/

| Module | Purpose |
|--------|---------|
| `project.py` | CFA project management, v1/v2 support, `get_project_paths()` |
| `analyzers/*.py` | Language analyzers (TypeScript, Python, Rust) |
| `lsp/manager.py` | LSP server lifecycle management |
| `lsp/symbols.py` | Symbol operations (find, replace, rename) |
| `workflow/onboarding.py` | Project onboarding context generation |
| `workflow/reflection.py` | Meta-cognition tools (think_*) |
| `memory_store.py` | SQLite-based persistent memory |
| `contract_parser.py` | Contract parsing and validation |
| `dependency_analyzer.py` | Dependency graph analysis |

### Supported Languages (LSP)
- Python, TypeScript, JavaScript
- Rust, Go, Java
- C/C++, C#, Ruby, PHP

## Data Flow

```
Session Start
    │
    ▼
workflow.onboard → Load full project context
    │
    ▼
task.start → Record task goal
    │
    ▼
symbol.find / file.search → Explore codebase
    │
    ▼
workflow.think_info → Reflect on findings
    │
    ▼
workflow.think_task → Validate approach
    │
    ▼
symbol.replace / file.* → Make changes
    │
    ▼
workflow.think_done → Verify completion
    │
    ▼
workflow.summarize → Generate summary
    │
    ▼
task.complete + memory.set → Complete & learn
```

## Current State

- ✅ CFA v2.0 with src/ structure
- ✅ Serena integration complete
- ✅ 51 MCP tools registered
- ✅ LSP support with fallback mode
- ✅ Workflow meta-cognition tools
- ✅ Persistent memory system
- ✅ Backwards compatible with CFA v1

## Key Design Decisions

1. **Serena Integration**: Adapted all 30 Serena tools to CFA architecture
2. **LSP with Fallback**: Full LSP when available, regex fallback otherwise
3. **Workflow Meta-cognition**: Think tools for structured AI reflection
4. **Dynamic Paths**: `get_project_paths()` for v1/v2 auto-detection
5. **Unified Memory**: SQLite for project-specific learnings
6. **Multi-language**: 30+ languages via multilspy

## Version
- **v0.2.0** - CFA + Serena (51 tools)
