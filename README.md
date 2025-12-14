# Context-First Architecture v2 + Serena

A comprehensive AI-assisted development framework combining architecture optimization for LLMs with semantic code analysis.

## What is CFA v2?

**CFA v2** is a complete framework that integrates:

- **Context-First Architecture**: Project structure optimized for LLM context windows
- **Serena Integration**: Semantic code analysis via Language Server Protocol (LSP)
- **44 MCP Tools**: Optimized toolkit for AI-assisted development
- **Workflow Meta-cognition**: Structured thinking tools for AI agents
- **Multi-language Support**: 30+ languages including Python, TypeScript, Rust, Go, Java, C/C++

## Philosophy

LLMs need dense, organized information to work effectively. CFA v2 provides:

1. **Contracts-First Design**: Define interfaces before implementation
2. **Semantic Code Operations**: LSP-powered symbol manipulation
3. **Persistent Memory**: Project knowledge across sessions
4. **Structured Workflows**: Guided AI thinking patterns
5. **Flat, Navigable Structure**: Easy context loading

## Project Structure (v2)

```
project/
├── .claude/
│   ├── map.md              # Project navigation map (auto-generated)
│   ├── settings.json       # CFA configuration
│   ├── decisions.md        # Architecture Decision Records (ADRs)
│   └── current-task.md     # Session continuity
│
├── contracts/
│   └── *.contract.md       # Interface definitions (WHAT, not HOW)
│
├── src/                    # Source code (v2 standard)
│   ├── core/               # Core business logic
│   ├── features/           # Feature implementations
│   └── shared/             # Shared utilities and types
│
├── tests/                  # Test files
└── claudedocs/             # AI-specific documentation
```

## MCP Tools (44 Total)

### CFA Core (20 tools)

**Project Management**
- `project.init` - Create new CFA v2 project
- `project.scan` - Update map.md from codebase
- `project.migrate` - Convert existing projects to v2

**Contracts**
- `contract.create` - Generate contracts from code
- `contract.validate` - Validate implementation vs contract
- `contract.diff` - Compare contract and code
- `contract.sync` - Sync contracts with code changes

**Tasks & Context**
- `task.start` - [PRIMARY] Begin new task
- `task.update` - Update task progress
- `task.complete` - Complete task
- `context.load` - Load full project context
- `context.optimize` - Optimize for token limits

**Analysis**
- `dependency.analyze` - Analyze dependencies
- `pattern.detect` - Detect code patterns
- `impact.analyze` - Calculate change impact
- `coupling.analyze` - Analyze feature coupling

**Documentation**
- `docs.generate` - Generate documentation
- `map.auto_update` - Auto-update map.md
- `test.coverage_map` - Map test coverage

### Symbol Tools - Serena (8 tools)

Semantic code operations via LSP with regex fallback:

- `symbol.find` - [PRIMARY] Find symbols by name across project
- `symbol.overview` - Get file symbol hierarchy
- `symbol.references` - Find all symbol references
- `symbol.replace` - [PRIMARY] Replace symbol body
- `symbol.insert` - Insert content before/after symbol (position parameter)
- `symbol.rename` - Rename symbol across project
- `lsp.status` - Get LSP server status
- `lsp.restart` - Restart LSP server(s)

### File Tools - Serena (7 tools)

Enhanced file operations respecting CFA structure:

- `file.read` - Read with optional line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Text search/replace. Use symbol.replace for code
- `file.edit_lines` - Line operations (delete/replace/insert)
- `file.search` - [PRIMARY] Search across files (grep)

### Workflow Tools - Serena (4 tools)

Meta-cognition for structured AI thinking:

- `workflow.onboard` - [START HERE] Load project context (includes check mode)
- `workflow.reflect` - Meta-cognition (info/task/done types)
- `workflow.summarize` - Summarize changes
- `workflow.instructions` - Get workflow guide

### Memory Tools (5 tools)

Persistent project knowledge:

- `memory.set` - [PRIMARY] Store learning (includes append mode)
- `memory.get` - Retrieve by key
- `memory.search` - Search by query/tags
- `memory.list` - List all memories
- `memory.delete` - Delete memory

---

## MCP Design Philosophy (AI Agent Perspective)

This MCP server was designed with AI agents as the primary users. The following design decisions were made to optimize for agent usability.

### Why 44 Tools Instead of 51?

We consolidated redundant tools to reduce cognitive load while maintaining full functionality:

| Before | After | Change |
|--------|-------|--------|
| `workflow.think_info` + `think_task` + `think_done` | `workflow.reflect` with type parameter | 3 → 1 |
| `workflow.onboard` + `check_onboard` | `workflow.onboard` with check_only parameter | 2 → 1 |
| `symbol.insert_before` + `insert_after` | `symbol.insert` with position parameter | 2 → 1 |
| `file.delete_lines` + `replace_lines` + `insert_at_line` | `file.edit_lines` with operation parameter | 3 → 1 |
| `memory.set` + `memory.edit` | `memory.set` with append parameter | 2 → 1 |

**Consolidation Principle**: If tools differ only by a single parameter, they should be consolidated into one tool with that parameter exposed.

### Tool Naming Conventions

- **Prefix groups**: `symbol.*`, `file.*`, `workflow.*` enable quick scanning and discovery
- **Verb-first for actions**: `find`, `replace`, `insert` immediately convey the operation
- **No abbreviations**: `workflow.onboard` not `wf.onb` - clarity over brevity

### Description Guidelines

Descriptions are written for AI agents who need to quickly decide which tool to use:

1. **Max 60 characters** when possible - optimized for tool listing scan
2. **Include WHEN to use**, not just WHAT it does
3. **Mark primary tools** with indicators: `[START HERE]`, `[PRIMARY]`
4. **Reference alternatives**: "Use symbol.replace for code changes"

### Tool Hierarchy

Not all tools are equal. Some are used frequently, others for specific situations:

**Always Start With:**
- `workflow.onboard` - First call in every session

**Primary Tools (80% of usage):**
- `symbol.find` → `symbol.replace` / `symbol.rename`
- `file.search` → `file.read`
- `task.start` → `task.complete`
- `memory.set`

**Secondary Tools (specific use cases):**
- Analysis tools (`dependency.analyze`, `coupling.analyze`, `impact.analyze`)
- Contract tools (`contract.validate`, `contract.diff`, `contract.sync`)
- LSP management (`lsp.status`, `lsp.restart`)

### Anti-Patterns Avoided

1. **Tool explosion**: Not creating separate tools for minor variations (e.g., separate tools for "insert before" vs "insert after")
2. **Vague descriptions**: Every description answers "when should I use this?"
3. **Hidden dependencies**: Tools that require other tools are explicitly documented
4. **Parameter overload**: Max 5-6 parameters per tool, sensible defaults for all optional parameters

### Consolidated Tool Reference

```
# Workflow reflection (was 3 tools)
workflow.reflect(type="info|task|done", content, context?, questions?, concerns?, tests_passed?)

# Workflow onboarding (was 2 tools)
workflow.onboard(check_only=False, include_contracts=True, include_decisions=True)

# Symbol insertion (was 2 tools)
symbol.insert(symbol_name, content, position="before|after")

# File line operations (was 3 tools)
file.edit_lines(operation="delete|replace|insert", lines, content?, start_line?, end_line?, insert_after?)

# Memory storage (was 2 tools)
memory.set(key, value, tags?, append=False)
```

---

## Installation

### Using pip

```bash
# Basic installation
pip install context-first-architecture

# With LSP support (recommended)
pip install context-first-architecture[lsp]

# With all extras
pip install context-first-architecture[all]
```

### Using uv (faster)

```bash
# Basic installation
uv pip install context-first-architecture

# With LSP support
uv pip install "context-first-architecture[lsp]"
```

## MCP Configuration

### Claude Desktop / Claude Code

Add to your MCP settings file (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):

#### Using uvx (Recommended)

```json
{
  "mcpServers": {
    "cfa": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Rixmerz/context-first-arch.git",
        "cfa-server"
      ]
    }
  }
}
```

#### Using installed package

```json
{
  "mcpServers": {
    "cfa": {
      "command": "cfa-server",
      "args": []
    }
  }
}
```

## Quick Start

### 1. Create New Project

```bash
# Using MCP tool
cfa project.init --path ./my-app --name "My App" --languages python typescript
```

Creates:
```
my-app/
├── .claude/
│   ├── map.md
│   ├── settings.json
│   ├── decisions.md
│   └── current-task.md
├── contracts/
├── src/
│   ├── core/
│   ├── features/
│   └── shared/
└── tests/
```

### 2. Onboard to Project

```bash
# Load full project context (ALWAYS START HERE)
cfa workflow.onboard --path ./my-app

# Check if re-onboarding needed
cfa workflow.onboard --path ./my-app --check-only
```

### 3. Start Working

```bash
# Start a task
cfa task.start --path ./my-app --goal "Implement user authentication"

# Use symbol tools for code changes
cfa symbol.find --path ./my-app --name "authenticate"
cfa symbol.replace --path ./my-app --file "src/auth.py" --symbol "authenticate" --new-body "..."

# Complete task
cfa task.complete --path ./my-app --summary "Auth complete with JWT"
```

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

## Configuration

Create `.claude/settings.json` in your project:

```json
{
  "cfa_version": "2.0",
  "source_root": "src",
  "project_name": "My App",
  "languages": ["python", "typescript"],
  "lsp": {
    "enabled": true,
    "languages": ["python", "typescript", "rust"]
  }
}
```

## Language Support

Via LSP (multilspy):
- Python, TypeScript, JavaScript
- Rust, Go, Java
- C/C++, C#, Ruby, PHP
- And 20+ more languages

When LSP is unavailable, tools automatically fall back to regex-based analysis.

## Architecture Principles

### 1. Contracts First
Define interfaces before implementation. Contracts are the source of truth.

### 2. Flat Structure
Maximum 2-3 levels of nesting. Easy navigation for LLMs.

### 3. Semantic Operations
Use symbol tools instead of text manipulation when possible.

### 4. Persistent Context
Store learnings in memory for future sessions.

### 5. Structured Reflection
Use workflow tools for meta-cognition before and after work.

## What Makes CFA v2 Different?

| Feature | Traditional | CFA v2 |
|---------|------------|--------|
| Structure | Deep nesting | Flat (max 2-3 levels) |
| Documentation | Scattered | Centralized in .claude/ |
| Code Changes | Text manipulation | Semantic via LSP |
| Context Loading | Manual file reads | One-call onboarding |
| Memory | Session-only | Persistent SQLite |
| Thinking | Implicit | Explicit via workflow tools |

## Best Practices

### Do This

- Start every session with `workflow.onboard`
- Use `symbol.replace` for function changes (not `file.replace`)
- Store insights with `memory.set` after discoveries
- Validate with `workflow.reflect` tools before marking complete
- Keep contracts synchronized with `contract.sync`

### Avoid This

- Don't skip onboarding - it's essential for context
- Don't use text replacement for semantic operations
- Don't forget to store learnings in memory
- Don't work without contracts for core features
- Don't create deep directory hierarchies

## Examples

### Find and Modify a Function

```bash
# Find function
cfa symbol.find --path . --name "calculate_total"

# Replace implementation
cfa symbol.replace --path . --file "src/billing.py" \
  --symbol "calculate_total" \
  --new-body "return sum(items) * (1 + tax_rate)"
```

### Rename Across Project

```bash
# Semantic rename (updates all references)
cfa symbol.rename --path . --file "src/user.py" \
  --old-name "getUserData" \
  --new-name "get_user_profile"
```

### Search and Analyze

```bash
# Search for pattern
cfa file.search --path . --pattern "TODO:" --file-pattern "*.py"

# Analyze dependencies
cfa dependency.analyze --path . --file "src/core/auth.py"
```

## Documentation

- [Serena Integration Guide](claudedocs/Serena_Integration.md)
- [CFA v2 Architecture](claudedocs/CFA_v2_Architecture.md)
- [Architecture Map](.claude/map.md)

## Repository

GitHub: https://github.com/Rixmerz/context-first-arch

## Version

**v0.2.1** - MCP Tool Consolidation (44 tools, optimized for AI agents)

## License

MIT
