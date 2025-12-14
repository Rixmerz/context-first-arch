# CFA + Serena Integration

## Overview

Context-First Architecture (CFA) v2.0 now integrates Serena's semantic code analysis capabilities, providing a comprehensive AI-assisted development framework with **51 MCP tools**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CFA + Serena MCP Server                      │
│                        (51 Tools)                               │
├─────────────────────────────────────────────────────────────────┤
│  CFA Core (20)  │  Memory (6)  │  Symbol (9)  │  File (9)  │  Workflow (7)  │
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

### 2. Memory Tools (6)

Persistent project knowledge storage using SQLite.

- `memory.set` - Store learning
- `memory.get` - Retrieve by key
- `memory.search` - Search by query/tags
- `memory.list` - List all memories
- `memory.edit` - Edit existing memory
- `memory.delete` - Delete memory

### 3. Symbol Tools (9) - Serena Integration

Semantic code operations via LSP (Language Server Protocol).

- `symbol.find` - Find symbols by name
- `symbol.overview` - Get file symbol hierarchy
- `symbol.references` - Find all references
- `symbol.replace` - Replace symbol body
- `symbol.insert_after` - Insert after symbol
- `symbol.insert_before` - Insert before symbol
- `symbol.rename` - Rename across project
- `lsp.status` - Get LSP server status
- `lsp.restart` - Restart LSP server(s)

**Supported Languages** (via multilspy):
- Python, TypeScript, JavaScript
- Rust, Go, Java
- C/C++, C#, Ruby, PHP

### 4. File Tools (9) - Serena Integration

Enhanced file operations respecting CFA structure.

- `file.read` - Read with line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Search and replace
- `file.delete_lines` - Delete specific lines
- `file.replace_lines` - Replace line range
- `file.insert_at_line` - Insert at line
- `file.search` - Search across files (grep)

### 5. Workflow Tools (7) - Serena Integration

Meta-cognition and reflection for AI agents.

- `workflow.onboard` - Generate project context
- `workflow.check_onboard` - Verify onboarding status
- `workflow.think_info` - Reflect on information
- `workflow.think_task` - Validate approach
- `workflow.think_done` - Verify completion
- `workflow.summarize` - Summarize changes
- `workflow.instructions` - Get CFA workflow guide

## Recommended Workflow

```
Session Start:
1. workflow.onboard          → Load full project context
2. workflow.check_onboard    → Verify context freshness

Task Execution:
3. task.start                → Record task goal
4. symbol.find / file.search → Explore codebase
5. workflow.think_info       → Reflect on findings
6. workflow.think_task       → Validate approach
7. symbol.replace / file.*   → Make changes
8. workflow.think_done       → Verify completion
9. workflow.summarize        → Generate summary
10. task.complete            → Mark done

Session End:
11. memory.set               → Store learnings
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
workflow.think_info → After gathering information
workflow.think_task → Before implementation
workflow.think_done → Before marking complete
```

### 4. Store Learnings
```
memory.set → Persist insights for future sessions
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
| Memory | 6 | CFA + Serena |
| Symbol | 9 | Serena |
| File | 9 | Serena |
| Workflow | 7 | Serena |
| **Total** | **51** | |

## Version History

- **v0.2.0** - Serena integration (51 tools)
- **v0.1.x** - CFA Core (23 tools)
