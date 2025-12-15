# Context-First Architecture v3

## Purpose
Unified MCP server providing **70 tools** for AI-assisted development combining:
- **CFA v3**: Knowledge Graph with intelligent context retrieval and omission transparency
- **CFA v2**: Architecture optimized for LLM context (contracts, features, dependencies)
- **Serena**: Semantic code analysis via LSP (symbols, references, refactoring)

## Entry Points
- `src/mcp_server/server.py:main()` → MCP server (68 tools)
- `cfa` / `cfa-server` → CLI commands

---

## Knowledge Graph System (CFA v3) - NEW

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                  MCP Tools Layer (18 new tools)             │
├─────────────────────────────────────────────────────────────┤
│  kg.build    kg.retrieve    kg.expand    kg.search         │
│  kg.status   kg.get         kg.omitted   kg.related        │
│  kg.history  kg.blame       kg.diff                         │
│  rule.interpret  rule.confirm  rule.list  rule.batch        │
│  timeline.checkpoint  timeline.compare  timeline.rollback   │
├─────────────────────────────────────────────────────────────┤
│                  Core Modules (~4,900 LOC)                  │
├─────────────────────────────────────────────────────────────┤
│  models.py      storage.py      retriever.py               │
│  chunker.py     graph_builder.py compressor.py             │
│  git_chunker.py business_rules.py timeline.py              │
├─────────────────────────────────────────────────────────────┤
│                SQLite + FTS5 (BM25 ranking)                 │
└─────────────────────────────────────────────────────────────┘
```

### ChunkTypes (10)
| Type | Description |
|------|-------------|
| SOURCE_FILE | Complete source file |
| FUNCTION | Function/method definition |
| CLASS | Class definition |
| TEST | Test file/function |
| CONTRACT | CFA contract |
| CONFIG | Configuration file |
| METADATA | Project metadata |
| COMMIT | Git commit |
| BUSINESS_RULE | Detected business rule |
| SNAPSHOT | Timeline snapshot |

### EdgeTypes (11)
| Type | Description |
|------|-------------|
| CALLS | Function calls another |
| IMPORTS | Module imports another |
| INHERITS | Class inherits from another |
| CONTAINS | File contains function/class |
| TESTED_BY | Code is tested by test |
| IMPLEMENTS | Implements contract |
| VALIDATES | Rule validates code |
| MODIFIED_IN | Changed in commit |
| PRECEDED_BY | Snapshot ordering |
| CONFIGURED_BY | Uses config |
| FAILED_AT | Error in commit |

### Key Concepts

**Omission Transparency** (Critical Feature)
Every retrieval reports what was NOT loaded and why:
- `omitted_chunks`: List of chunks not loaded
- `omission_summary`: Human-readable summary
- `available_expansions`: What can be loaded next

**Compression Levels**
| Level | Name | Description |
|-------|------|-------------|
| 0 | FULL | Complete content with all comments |
| 1 | NO_COMMENTS | Code without comments |
| 2 | SIGNATURE_DOCSTRING | Signature + docstring only |
| 3 | SIGNATURE_ONLY | Just the signature |

**Business Rules Workflow**
```
Code with validation logic
         ↓
rule.interpret → AI proposes rules (status: PROPOSED)
         ↓
Human reviews
         ↓
rule.confirm → Confirm, correct, or reject
         ↓
Rule becomes CONFIRMED (or REJECTED)
```

### Knowledge Graph Tools (19)

**Core KG Tools (9)**
- `kg.build` - Build/update the Knowledge Graph
- `kg.status` - Get KG statistics
- `kg.retrieve` - [PRIMARY] Task-aware context retrieval with omission transparency
- `kg.expand` - Expand from specific chunk
- `kg.get` - Get specific chunk by ID
- `kg.search` - Full-text search
- `kg.omitted` - List omitted chunks
- `kg.related` - Find related chunks
- `kg.watch` - Control file watcher for auto-updates

**KG History Tools (3)**
- `kg.history` - View chunk change history
- `kg.blame` - See who changed code
- `kg.diff` - Compare chunks between commits

**Business Rules Tools (4)**
- `rule.interpret` - Extract rules from code
- `rule.confirm` - Confirm/correct/reject rule
- `rule.list` - List rules with filters (includes quick actions)
- `rule.batch` - Batch confirm/reject multiple rules

**Timeline Tools (3)**
- `timeline.checkpoint` - Create snapshot
- `timeline.compare` - Compare snapshots
- `timeline.rollback` - Rollback to snapshot

---

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

- ✅ CFA v3.0 with Knowledge Graph
- ✅ CFA v2.0 with src/ structure
- ✅ Serena integration complete
- ✅ 69 MCP tools registered (18 new KG tools)
- ✅ LSP support with fallback mode
- ✅ Workflow meta-cognition tools
- ✅ Persistent memory system
- ✅ Omission transparency (always know what was NOT loaded)
- ✅ Business Rules detection and confirmation
- ✅ Timeline snapshots and rollback
- ✅ Backwards compatible with CFA v1/v2

## Key Design Decisions

1. **Knowledge Graph (v3)**: Graph-based context with BM25 search + multi-hop traversal
2. **Omission Transparency**: Every retrieval reports omissions with reasons
3. **Business Rules**: AI proposes → Human confirms workflow for tacit knowledge
4. **Timeline Snapshots**: User vs Agent snapshots for safe exploration
5. **Serena Integration**: Adapted all 30 Serena tools to CFA architecture
6. **LSP with Fallback**: Full LSP when available, regex fallback otherwise
7. **Workflow Meta-cognition**: Think tools for structured AI reflection
8. **Dynamic Paths**: `get_project_paths()` for v1/v2/v3 auto-detection
9. **Unified Memory**: SQLite for project-specific learnings
10. **Multi-language**: 30+ languages via multilspy

## Version
- **v3.0.0** - CFA + Serena + Knowledge Graph (69 tools)
- **v0.2.0** - CFA + Serena (51 tools)
- **v0.1.0** - CFA Core
