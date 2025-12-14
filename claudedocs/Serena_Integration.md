# CFA + Serena Integration

## Overview

Context-First Architecture (CFA) v2.0 integrates Serena's semantic code analysis capabilities, providing a comprehensive AI-assisted development framework with **44 optimized MCP tools** (consolidated from 51 for improved AI agent usability).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CFA + Serena MCP Server                      │
│                        (44 Tools)                               │
├─────────────────────────────────────────────────────────────────┤
│  CFA Core (20)  │  Memory (5)  │  Symbol (8)  │  File (7)  │  Workflow (4)  │
├─────────────────┼──────────────┼──────────────┼────────────┼────────────────┤
│  project.*      │  memory.*    │  symbol.*    │  file.*    │  workflow.*    │
│  contract.*     │              │  lsp.*       │            │                │
│  task.*         │              │              │            │                │
│  decision.*     │              │              │            │                │
│  context.*      │              │              │            │                │
│  dependency.*   │              │              │            │                │
│  pattern.*      │              │              │            │                │
│  impact.*       │              │              │            │                │
│  coupling.*     │              │              │            │                │
│  docs.*         │              │              │            │                │
│  map.*          │              │              │            │                │
│  test.*         │              │              │            │                │
└─────────────────┴──────────────┴──────────────┴────────────┴────────────────┘
```

## Tool Consolidation (v0.2.1)

To improve AI agent usability, we consolidated redundant tools:

| Before (51 tools) | After (44 tools) | Rationale |
|-------------------|------------------|-----------|
| `workflow.think_info` + `think_task` + `think_done` | `workflow.reflect` with type parameter | Same functionality, single tool |
| `workflow.onboard` + `check_onboard` | `workflow.onboard` with check_only parameter | Related functionality unified |
| `symbol.insert_before` + `insert_after` | `symbol.insert` with position parameter | Differ only by position |
| `file.delete_lines` + `replace_lines` + `insert_at_line` | `file.edit_lines` with operation parameter | All line-based operations |
| `memory.set` + `memory.edit` | `memory.set` with append parameter | Set already implied edit |

**Principle**: If tools differ only by a single parameter, consolidate them.

## Tool Categories

### 1. CFA Core Tools (20)

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
- `task.start` - [PRIMARY] Begin new task
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

### 2. Memory Tools (5) - Consolidated

Persistent project knowledge storage using SQLite.

- `memory.set` - [PRIMARY] Store learning (supports append mode)
- `memory.get` - Retrieve by key
- `memory.search` - Search by query/tags
- `memory.list` - List all memories
- `memory.delete` - Delete memory

**Consolidated**: `memory.edit` → merged into `memory.set` with `append=True`

### 3. Symbol Tools (8) - Serena Integration

Semantic code operations via LSP (Language Server Protocol).

- `symbol.find` - [PRIMARY] Find symbols by name
- `symbol.overview` - Get file symbol hierarchy
- `symbol.references` - Find all references
- `symbol.replace` - [PRIMARY] Replace symbol body
- `symbol.insert` - Insert before/after symbol (position parameter)
- `symbol.rename` - Rename across project
- `lsp.status` - Get LSP server status
- `lsp.restart` - Restart LSP server(s)

**Consolidated**: `symbol.insert_before` + `symbol.insert_after` → `symbol.insert(position="before|after")`

**Supported Languages** (via multilspy):
- Python, TypeScript, JavaScript
- Rust, Go, Java
- C/C++, C#, Ruby, PHP

### 4. File Tools (7) - Serena Integration

Enhanced file operations respecting CFA structure.

- `file.read` - Read with line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Text search/replace. Use symbol.replace for code
- `file.edit_lines` - Line operations (delete/replace/insert)
- `file.search` - [PRIMARY] Search across files (grep)

**Consolidated**: `file.delete_lines` + `file.replace_lines` + `file.insert_at_line` → `file.edit_lines(operation="delete|replace|insert")`

### 5. Workflow Tools (4) - Serena Integration

Meta-cognition and reflection for AI agents.

- `workflow.onboard` - [START HERE] Load project context (includes check mode)
- `workflow.reflect` - Meta-cognition for info/task/done phases
- `workflow.summarize` - Summarize changes
- `workflow.instructions` - Get CFA workflow guide

**Consolidated**:
- `workflow.check_onboard` → merged into `workflow.onboard(check_only=True)`
- `workflow.think_info` + `workflow.think_task` + `workflow.think_done` → `workflow.reflect(type="info|task|done")`

## Recommended Workflow

```
Session Start:
1. workflow.onboard              → Load full project context

Task Execution:
2. task.start                    → Record task goal
3. symbol.find / file.search     → Explore codebase
4. workflow.reflect(type="info") → Reflect on findings
5. workflow.reflect(type="task") → Validate approach
6. symbol.replace / file.*       → Make changes
7. workflow.reflect(type="done") → Verify completion
8. workflow.summarize            → Generate summary
9. task.complete                 → Mark done

Session End:
10. memory.set                   → Store learnings
```

## Consolidated Tool Reference

```python
# Workflow reflection (was 3 tools)
workflow.reflect(
    type="info" | "task" | "done",
    content: str,
    context?: str,
    questions?: list,    # for info
    concerns?: list,     # for task
    tests_passed?: bool  # for done
)

# Workflow onboarding (was 2 tools)
workflow.onboard(
    check_only=False,
    include_contracts=True,
    include_decisions=True,
    max_context_size=50000
)

# Symbol insertion (was 2 tools)
symbol.insert(
    symbol_name: str,
    content: str,
    position="before" | "after"
)

# File line operations (was 3 tools)
file.edit_lines(
    operation="delete" | "replace" | "insert",
    lines: int | list | str,  # for delete/insert
    content?: str,            # for replace/insert
    start_line?: int,         # for replace
    end_line?: int,           # for replace
    insert_after?: bool       # for insert
)

# Memory storage (was 2 tools)
memory.set(
    key: str,
    value: str,
    tags?: list,
    append=False  # True to append instead of replace
)
```

## LSP Fallback Mode

When LSP servers are unavailable, symbol tools automatically fall back to regex-based analysis:

```python
# LSP Mode (when available)
- Precise symbol boundaries
- Cross-file reference tracking
- Semantic rename across project

# Fallback Mode (regex-based)
- Pattern matching for symbols
- File-local reference detection
- Text-based rename
```

## Installation

```bash
# Install with LSP support
pip install context-first-architecture[lsp]

# Or with all extras
pip install context-first-architecture[all]
```

## Configuration

In `.claude/settings.json`:
```json
{
  "cfa_version": "2.0",
  "source_root": "src",
  "lsp": {
    "enabled": true,
    "languages": ["python", "typescript"]
  }
}
```

## Best Practices

### 1. Always Onboard First
```
workflow.onboard → Ensures AI has full context
```

### 2. Use Symbol Tools for Code Changes
```
symbol.replace   → Better than file.replace for functions
symbol.rename    → Updates all references automatically
```

### 3. Reflect Before Acting
```
workflow.reflect(type="info") → After gathering information
workflow.reflect(type="task") → Before implementation
workflow.reflect(type="done") → Before marking complete
```

### 4. Store Learnings
```
memory.set → Persist insights for future sessions
memory.set(append=True) → Add to existing memory
```

### 5. Validate Against Contracts
```
contract.validate → Ensure implementation matches spec
contract.diff     → See detailed differences
```

## Tool Count Summary

| Category | Count | Source |
|----------|-------|--------|
| Project | 3 | CFA |
| Contract | 4 | CFA |
| Task | 3 | CFA |
| Decision/Context | 3 | CFA |
| Analysis | 4 | CFA |
| Documentation | 3 | CFA |
| Memory | 5 | CFA + Serena |
| Symbol | 8 | Serena |
| File | 7 | Serena |
| Workflow | 4 | Serena |
| **Total** | **44** | |

## Version History

- **v0.2.1** - Tool consolidation (44 tools, optimized for AI agents)
- **v0.2.0** - Serena integration (51 tools)
- **v0.1.x** - CFA Core (23 tools)
