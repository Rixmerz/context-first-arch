# Architecture Decisions

## 2026-01-08: CFA v4 - Radical Simplification

**Context**: CFA v1-v3 grew to 27+ tools with knowledge graphs, SQLite databases, LSP integration, and complex orchestration. The complexity wasn't providing proportional value.

**Decision**: Strip down to 4 essential tools:
- `cfa.onboard` - Load project context
- `cfa.remember` - Store knowledge
- `cfa.recall` - Retrieve knowledge
- `cfa.checkpoint` - Git-based safe points

**Reason**: "Architecture over indexing" - good project structure makes complex indexing unnecessary. Simple tools that do one thing well.

**Consequences**:
- Removed ~170 Python files
- Removed all SQLite databases
- Removed knowledge graph, chunking, RAG pipeline
- Removed LSP integration
- Single dependency: `mcp`

**Trade-offs**: Lost sophisticated retrieval → Gained simplicity and maintainability

---

## 2024-12-10: Initial CFA Framework

**Context**: Starting new MCP server for Context-First Architecture
**Decision**: Build as standalone MCP server with Python
**Reason**: MCP protocol enables Claude Code integration

---

## Previous Decisions (Historical)

The following decisions from v1-v3 are now obsolete but kept for reference:
- Multi-language analyzer support → Removed
- Dependency graph implementation → Removed
- Contract format → Removed
- Memory store with SQLite → Replaced with JSON
- Knowledge graph with BM25 → Removed
