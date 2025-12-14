# Context-First Architecture v2 + Serena

A comprehensive AI-assisted development framework combining architecture optimization for LLMs with semantic code analysis.

## What is CFA v2?

**CFA v2** is a complete framework that integrates:

- **Context-First Architecture**: Project structure optimized for LLM context windows
- **Serena Integration**: Semantic code analysis via Language Server Protocol (LSP)
- **51 MCP Tools**: Unified toolkit for AI-assisted development
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

## MCP Tools (51 Total)

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
- `task.start` - Begin new task
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

### Symbol Tools - Serena (9 tools)

Semantic code operations via LSP with regex fallback:

- `symbol.find` - Find symbols by name across project
- `symbol.overview` - Get file symbol hierarchy
- `symbol.references` - Find all symbol references
- `symbol.replace` - Replace symbol body
- `symbol.insert_after` - Insert after symbol
- `symbol.insert_before` - Insert before symbol
- `symbol.rename` - Rename symbol across project
- `lsp.status` - Get LSP server status
- `lsp.restart` - Restart LSP server(s)

### File Tools - Serena (9 tools)

Enhanced file operations respecting CFA structure:

- `file.read` - Read with optional line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Search and replace content
- `file.delete_lines` - Delete specific lines
- `file.replace_lines` - Replace line range
- `file.insert_at_line` - Insert at specific line
- `file.search` - Search across files (grep)

### Workflow Tools - Serena (7 tools)

Meta-cognition for structured AI thinking:

- `workflow.onboard` - Generate project context
- `workflow.check_onboard` - Verify onboarding status
- `workflow.think_info` - Reflect on information
- `workflow.think_task` - Validate approach
- `workflow.think_done` - Verify completion
- `workflow.summarize` - Summarize changes
- `workflow.instructions` - Get workflow guide

### Memory Tools (6 tools)

Persistent project knowledge:

- `memory.set` - Store learning
- `memory.get` - Retrieve by key
- `memory.search` - Search by query/tags
- `memory.list` - List all memories
- `memory.edit` - Edit existing memory
- `memory.delete` - Delete memory

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

### ✅ Do This

- Start every session with `workflow.onboard`
- Use `symbol.replace` for function changes (not `file.replace`)
- Store insights with `memory.set` after discoveries
- Validate with `workflow.think_*` tools before marking complete
- Keep contracts synchronized with `contract.sync`

### ❌ Avoid This

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

**v0.2.0** - CFA v2 + Serena Integration (51 tools)

## License

MIT
