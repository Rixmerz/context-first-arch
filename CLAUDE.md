# CLAUDE.md - CFA Project Instructions

This project uses **Context-First Architecture (CFA) v3** with 27 optimized MCP tools.

## Session Start Protocol

At the START of every session, you MUST:
1. Call `workflow.onboard(project_path=".")` to load project context
2. Call `kg.retrieve(task="<your task>")` to get task-relevant code
3. Call `memory.search(query="<task keywords>")` to check past learnings

**DO NOT start coding without context.** CFA provides intelligent retrieval.

## During Development

### Before Writing Code
- `kg.retrieve(task="...")` - Get relevant code context for your task
- `analyze.change(project_path=".")` - Check project patterns (without file_path)
- `rule.list(project_path=".")` - Check business rules that must be preserved

### After Modifying Functions
**CRITICAL:** After changing ANY function signature (parameters added/removed/reordered):
```
contract.check_breaking(project_path=".", symbol="function_name")
```
DO NOT mark task complete until `breaking_changes=[]`. Skipping causes runtime errors.

### Before Risky Changes
Before deleting files, major refactoring, or modifying core logic:
1. `analyze.change(project_path=".", file_path="...")` - Check impact/blast radius
2. If risk is high/critical: `safe_point.create(task_summary="...")` - Create checkpoint

### When Learning Something Important
When discovering project patterns, gotchas, or decisions:
```
memory.set(key="descriptive-key", value="what you learned", tags=["pattern", "gotcha"])
```
Future sessions will retrieve this knowledge.

## Recovery

### If Something Breaks
1. `safe_point.list(project_path=".")` - See available restore points
2. `safe_point.rollback(project_path=".", mode="preview")` - Preview what would be reverted
3. `safe_point.rollback(project_path=".", mode="execute")` - Actually rollback

### If Context Feels Incomplete
The `kg.retrieve` response includes omission info. To expand:
1. Review `omission_summary` in kg.retrieve response
2. `kg.context(project_path=".", mode="expand", chunk_id="...")` - Get more context

## Consolidated Tools Reference

CFA v3 uses mode/operation parameters for related functionality:

| Old Tools | New Unified Tool |
|-----------|------------------|
| `kg.expand`, `kg.get`, `kg.related` | `kg.context(mode="expand\|get\|related")` |
| `kg.history`, `kg.blame`, `kg.diff` | `kg.git(operation="history\|blame\|diff")` |
| `dependency.analyze`, `coupling.analyze` | `analyze.structure(target=...or None)` |
| `pattern.detect`, `impact.analyze` | `analyze.change(file_path=...or None)` |
| `contract.diff` | `contract.sync(preview=true)` |
| `rule.batch` | `rule.confirm(rule_ids=[...])` |
| `workflow.instructions` | `workflow.onboard(show_instructions=true)` |
| `project.scan` | `kg.build(update_map=true)` |

## Project: context-first-arch

This is the CFA framework itself. Key directories:
- `src/mcp_server/` - MCP server with 27 tools
- `src/features/` - Feature implementations (knowledge_graph, memory, rules, etc.)
- `src/core/` - Core utilities and analyzers

---

## Project-Specific Notes

<!-- Add project-specific conventions, gotchas, or instructions here -->
