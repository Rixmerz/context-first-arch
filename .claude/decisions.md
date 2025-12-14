# Architecture Decisions

## 2024-12-10: Initial CFA Framework

**Context**: Starting new MCP server for Context-First Architecture
**Decision**: Build as standalone MCP server with Python
**Reason**: MCP protocol enables Claude Code integration, Python provides rich ecosystem for code analysis
**Trade-offs**: Python performance vs ease of development → chose ease

## 2024-12-13: Multi-Language Analyzer Support

**Context**: Need to analyze TypeScript, Python, and Rust codebases
**Decision**: Plugin-based analyzer registry with language-specific implementations
**Reason**: Extensible design allows adding new languages without modifying core
**Trade-offs**: Complexity vs flexibility → chose flexibility

## 2024-12-13: Dependency Graph Implementation

**Context**: Need to track feature dependencies and circular references
**Decision**: Build in-memory directed graph with DFS cycle detection
**Reason**: Efficient for small-to-medium codebases, simple implementation
**Trade-offs**: Memory usage vs disk persistence → chose memory for speed

## 2024-12-13: Contract Format Decision

**Context**: Need standard format for feature contracts
**Decision**: Markdown with structured sections (Purpose, Interface, State, Dependencies)
**Reason**: Human-readable, version-controllable, LLM-friendly
**Trade-offs**: Loose schema vs strict schema → chose loose for flexibility

## 2024-12-14: CFA v2.0 Architecture

**Context**: Modern frameworks (Vite, Next.js) expect src/ directory
**Decision**: Create CFA v2 with configurable source_root, default to src/
**Reason**: Framework compatibility while maintaining CFA principles
**Trade-offs**: Breaking change vs compatibility → chose backwards compatibility

**Implementation**:
- Added `cfa_version` and `source_root` to CFAProject
- Created `get_project_paths()` for auto-detection
- Updated all 23 tools to use dynamic paths
- Maintained full v1 support

## 2024-12-14: Self-Migration to v2

**Context**: Framework project should exemplify its own architecture
**Decision**: Migrate context-first project itself to CFA v2
**Reason**: Dogfooding - use our own architecture standards
**Trade-offs**: Migration effort vs consistency → chose consistency

**Changes**:
- Created src/ directory
- Moved core/ → src/core/
- Moved mcp_server/ → src/mcp_server/
- Updated all imports to src.core/src.mcp_server prefix
- Created full .claude/ configuration

## 2024-12-14: Memory Store Implementation

**Context**: Need persistent storage for project learnings
**Decision**: SQLite database in .claude/memory.db
**Reason**: Zero-dependency, file-based, supports tags and search
**Trade-offs**: SQLite vs document DB → chose SQLite for simplicity

## 2024-12-14: Test Coverage Mapping

**Context**: Need to map tests to contract functions
**Decision**: Pattern-based test name matching with heuristics
**Reason**: Works across frameworks (Jest, pytest, Rust) without parsing
**Trade-offs**: Accuracy vs simplicity → chose simplicity with 80% accuracy

## Pending Decisions

### Versioning Strategy
**Question**: How to version CFA projects and framework?
**Options**:
1. Semantic versioning for framework
2. Date-based versioning
3. No explicit versioning

**Current**: Using "2.0" as major version marker

### Multi-Project Workspaces
**Question**: How to handle monorepos with multiple CFA projects?
**Options**:
1. Root .claude/ with shared context
2. Independent .claude/ per project
3. Hybrid approach

**Current**: Documented but not implemented
