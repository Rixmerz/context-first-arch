# Context-First Architecture v3

AI-assisted development framework with **intelligent context retrieval** and **omission transparency**.

## What Makes CFA v3 Special?

**Knowledge Graph** - Never wonder what your AI assistant knows or doesn't know. Every context retrieval shows:
- ✅ **What was loaded** and why
- ⚠️ **What was omitted** and why
- 🔍 **What you can expand** next

Combined with **72 MCP tools** across 10 feature categories, CFA v3 provides complete AI-assisted development workflow.

---

## Quick Start

### 1. Install

```bash
pip install context-first-architecture

# Or with LSP support (recommended)
pip install "context-first-architecture[lsp]"
```

### 2. Configure for Claude Desktop / Claude Code

Add to your MCP settings (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):

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

### 3. See It In Action

```python
# Build knowledge graph of your project
kg.build(project_path=".")

# Get task-relevant context with transparency
result = kg.retrieve(
    task="understand authentication flow",
    token_budget=10000
)

# See what was loaded
print(result["context_markdown"])

# See what was omitted (the key feature!)
print(result["omission_summary"])
# "156 chunks omitted (350K tokens). Primary reason: token_budget"

# Expand what you need
expanded = kg.expand(
    chunk_id=result["available_expansions"][0]["chunk_id"]
)
```

---

## Core Concepts

### Knowledge Graph (CFA v3)

Indexes your codebase as interconnected chunks with intelligent retrieval:

- **Smart Retrieval**: BM25 search + multi-hop graph traversal
- **Omission Transparency**: Always know what's NOT loaded and why
- **Progressive Disclosure**: Load signatures first, expand as needed
- **Compression Levels**: Control detail vs. tokens (0-3)
- **Git Integration**: Historical analysis and blame tracking
- **Business Rules**: Capture tacit knowledge automatically

**See more**: [Knowledge Graph Guide](claudedocs/knowledge-graph-guide.md)

### Semantic Operations (Serena)

LSP-powered code manipulation that understands your language:

- Find, rename, replace symbols across entire project
- Reference tracking and navigation
- 30+ languages supported with regex fallback

### Architecture (CFA v2)

LLM-optimized project structure foundation:

- **Contracts-first design**: Define interfaces before implementation
- **Flat structure**: Maximum 2-3 nesting levels for easy navigation
- **Persistent memory**: Store learnings across sessions
- **Structured workflows**: Guided thinking patterns for AI agents

---

## Features Overview

### 🧠 Knowledge Graph (19 tools)

Build and intelligently query codebase index:

**Core Tools:**
- `kg.build` - Build or update Knowledge Graph (incremental or full)
- `kg.retrieve` - [PRIMARY] Task-aware context retrieval with omission transparency
- `kg.expand` - Expand context from specific chunk
- `kg.search` - Full-text BM25 search across graph
- `kg.status` - Get graph statistics and status
- `kg.get` - Retrieve specific chunk by ID
- `kg.omitted` - List chunks omitted from last retrieval
- `kg.related` - Find related chunks via graph edges

**Git & History:**
- `kg.history` - Git history integration
- `kg.blame` - Commit and author tracking
- `kg.diff` - Diff between versions
- `kg.watch` - Auto-rebuild on file changes

**Unique Capabilities:**
- Omission transparency in every response
- Multi-hop graph traversal
- Compression levels (signatures → full content)
- Business rule integration

**Learn more:** [Knowledge Graph Guide](claudedocs/knowledge-graph-guide.md)

### 📋 Business Rules (4 tools)

Capture and validate tacit knowledge automatically:

- `rule.interpret` - AI proposes rules from code patterns
- `rule.confirm` - Human confirms, corrects, or rejects rules
- `rule.list` - List all business rules
- `rule.batch` - Batch operations on rules

Human-in-the-loop workflow for validating AI-detected patterns.

**Learn more:** [Business Rules Guide](claudedocs/business-rules-guide.md)

### ⏱️ Timeline (3 tools)

Project snapshots and safe rollback:

- `timeline.checkpoint` - Create project snapshot with description
- `timeline.compare` - Compare snapshots
- `timeline.rollback` - Safely restore to previous snapshot

**Learn more:** [Timeline Guide](claudedocs/timeline-guide.md)

### 🔧 Symbol Tools - Serena (8 tools)

Semantic code operations via LSP:

- `symbol.find` - [PRIMARY] Find symbols by name across project
- `symbol.replace` - [PRIMARY] Replace symbol body semantically
- `symbol.rename` - Rename symbol and all references
- `symbol.insert` - Insert content before/after symbol
- `symbol.references` - Find all symbol references
- `symbol.overview` - Get file symbol hierarchy
- `lsp.manage` - Manage LSP servers

### 📁 File Tools - Serena (7 tools)

Enhanced file operations respecting CFA structure:

- `file.read` - Read file with optional line range
- `file.create` - Create new file
- `file.list` - List directory contents
- `file.find` - Find files by pattern
- `file.replace` - Text search and replace
- `file.edit_lines` - Delete, replace, or insert lines
- `file.search` - [PRIMARY] Search across files (grep)

### 📝 Contracts (4 tools)

Interface-first development:

- `contract.create` - Generate contracts from code
- `contract.validate` - Validate implementation vs contract
- `contract.diff` - Compare contract and code changes
- `contract.sync` - Sync contracts with code changes

### 📊 Analysis (4 tools)

Codebase intelligence and impact analysis:

- `dependency.analyze` - Analyze dependencies
- `pattern.detect` - Detect code patterns
- `impact.analyze` - Calculate change impact
- `coupling.analyze` - Analyze feature coupling

### 🎯 Project Management (3 tools)

CFA project lifecycle:

- `project.init` - Create new CFA v3 project
- `project.scan` - Update project map from codebase
- `project.migrate` - Convert existing projects to CFA

### 💭 Workflow (4 tools - Serena)

Structured AI thinking and reflection:

- `workflow.onboard` - [START HERE] Load full project context
- `workflow.reflect` - Meta-cognition (info/task/done types)
- `workflow.summarize` - Generate change summary
- `workflow.instructions` - Get workflow guide

### 💾 Memory (5 tools)

Persistent project knowledge:

- `memory.set` - [PRIMARY] Store learning with optional append mode
- `memory.get` - Retrieve memory by key
- `memory.search` - Search memories by query/tags
- `memory.list` - List all memories
- `memory.delete` - Delete memory

### 🚀 Orchestration (11 tools - Nova)

Advanced workflow management and loop control:

- `agent.route` - Route to appropriate agent
- `agent.spawn` - Spawn new agent for task
- `agent.status` - Get agent status
- `loop.configure` - Configure execution loop
- `loop.iterate` - Execute single loop iteration
- `loop.status` - Get loop status
- `loop.stop` - Stop running loop
- `safe_point.create` - Create git safe point
- `safe_point.list` - List safe points
- `safe_point.rollback` - Rollback to safe point
- And more...

---

## Installation

### Using pip

```bash
# Basic installation
pip install context-first-architecture

# With LSP support (recommended for symbol operations)
pip install "context-first-architecture[lsp]"

# With everything
pip install "context-first-architecture[all]"
```

### Using uv (faster)

```bash
# Basic
uv pip install context-first-architecture

# With LSP
uv pip install "context-first-architecture[lsp]"
```

### Optional Dependencies

- `[lsp]` - Language Server Protocol support (30+ languages)
- `[watcher]` - Auto-rebuild Knowledge Graph on file changes
- `[tree-sitter]` - Tree-sitter parsing for advanced analysis
- `[dev]` - Development tools (pytest, black, ruff)
- `[all]` - Everything combined

---

## Configuration

Create `.claude/settings.json` in your project:

```json
{
  "cfa_version": "3.0",
  "source_root": "src",
  "project_name": "My App",
  "languages": ["python", "typescript"],
  "lsp": {
    "enabled": true,
    "languages": ["python", "typescript", "rust"]
  },
  "knowledge_graph": {
    "auto_build": true,
    "incremental": true,
    "compression_default": 1,
    "max_chunk_size": 2000
  }
}
```

---

## Recommended Workflow

### Session Start (v3)

```python
# 1. Check Knowledge Graph status
kg.status()

# 2. Update if needed (incremental)
kg.build(incremental=True)

# 3. Load project context
workflow.onboard()
```

### Task Execution (v3)

```python
# 2. Get task-relevant context
result = kg.retrieve(
    task="implement user authentication",
    symbols=["User", "authenticate"],
    include_tests=True,
    token_budget=10000
)

# 3. Review what was loaded and omitted
print(result["omission_summary"])

# 4. Expand if something important was omitted
if result["stats"]["chunks_omitted"] > 100:
    kg.expand(chunk_id=result["available_expansions"][0]["chunk_id"])

# 5. Make code changes
symbol.replace(file="src/auth.py", symbol="authenticate", new_body="...")

# 6. Reflect on your work
workflow.reflect(type="done", content="Implementation complete")
```

### Session End (v3)

```python
# 7. Store learnings for next session
memory.set(
    key="auth_implementation",
    value="Key insight about token validation",
    tags=["auth", "jwt"]
)

# 8. Create checkpoint
timeline.checkpoint(description="Authentication feature complete")
```

---

## Project Structure (v3)

```
project/
├── .claude/
│   ├── map.md                    # Project navigation (auto-generated)
│   ├── settings.json             # CFA configuration
│   ├── decisions.md              # Architecture Decision Records
│   ├── knowledge_graph.db        # Knowledge Graph (auto-built)
│   └── memory.db                 # Memory store
│
├── contracts/
│   └── *.contract.md             # Interface definitions
│
├── src/
│   ├── core/                     # Core business logic
│   ├── features/                 # Feature implementations
│   └── shared/                   # Shared utilities
│
├── tests/                        # Test files
└── claudedocs/                   # AI-specific documentation
```

---

## CFA v3 vs v2 vs Traditional

| Feature | Traditional | CFA v2 | CFA v3 |
|---------|------------|--------|--------|
| **Context Loading** | Manual reads | `workflow.onboard` | `kg.retrieve` (task-aware) |
| **Omission Awareness** | None | None | **✅ Full transparency** |
| **Code Search** | grep/ripgrep | `file.search` | **✅ BM25 + graph traversal** |
| **Symbol Ops** | Text edit | **✅ LSP-based** | LSP + graph-aware |
| **Business Rules** | Implicit | Contracts | **✅ AI-detected + human confirmed** |
| **Project History** | git log | git log | **✅ Timeline snapshots** |
| **Token Efficiency** | Manual | Manual | **✅ Compression levels (0-3)** |
| **Memory** | Session-only | **✅ Persistent SQLite** | **✅ KG-integrated** |
| **Change Impact** | Manual | `impact.analyze` | **✅ Graph-based calculation** |

---

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────┐
│  MCP Tools Layer (72 tools)     │
├─────────────────────────────────┤
│  Feature Modules (10 features)  │
├─────────────────────────────────┤
│  Core Components & Storage      │
└─────────────────────────────────┘
```

### Feature Modules

1. **knowledge_graph** - Chunking, retrieval, graph building
2. **symbol** - LSP-based semantic operations
3. **file** - File operations respecting CFA structure
4. **analysis** - Dependency, impact, pattern analysis
5. **contract** - Interface definitions and validation
6. **memory** - Persistent learning storage
7. **workflow** - Structured thinking and reflection
8. **rules** - Business rule capture and validation
9. **timeline** - Snapshots and safe rollback
10. **orchestration** - Agent routing and loop control

---

## Language Support

Via LSP (multilspy):
- Python, TypeScript, JavaScript
- Rust, Go, Java
- C/C++, C#, Ruby, PHP, Kotlin
- And 20+ more languages

When LSP unavailable, tools fallback to regex-based analysis.

---

## Examples

### Knowledge Graph Workflow

```python
# 1. Build graph on first run
kg.build(project_path=".")

# 2. For each task, retrieve context transparently
result = kg.retrieve(
    task="fix login bug",
    symbols=["authenticate", "validate_token"],
    compression=1,  # No comments for efficiency
    token_budget=8000
)

# 3. See exactly what was included and excluded
loaded = result["stats"]["chunks_loaded"]          # 25 chunks
omitted = result["stats"]["chunks_omitted"]        # 234 chunks
tokens_used = result["stats"]["tokens_used"]       # 7,856 tokens

print(f"Loaded: {loaded}, Omitted: {omitted}")
print(f"Omission reason: {result['omission_summary']}")

# 4. Expand specific chunks if needed
if "validate_token" in str(result["omitted_chunks"]):
    expanded = kg.expand(
        chunk_id=omitted_chunks[0]["id"],
        direction="all"  # Include dependencies and dependents
    )
```

### Symbol Manipulation

```python
# Find function across project
matches = symbol.find(path=".", name="authenticate")

# Rename with semantic understanding
symbol.rename(
    file="src/auth.py",
    old_name="authenticate",
    new_name="validate_credentials"
)

# Replace function body
symbol.replace(
    file="src/auth.py",
    symbol="validate_token",
    new_body="""
def validate_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return True
    except jwt.InvalidTokenError:
        return False
"""
)
```

### Business Rules Capture

```python
# 1. AI proposes rules from validation logic
rules = rule.interpret(
    task="understand password validation",
    symbols=["validate_password"]
)

# 2. Review AI proposals
for rule in rules:
    print(f"Rule: {rule['content']}")
    print(f"Confidence: {rule['confidence']}")

# 3. Human confirms or corrects
rule.confirm(
    rule_id=rules[0]["id"],
    status="confirmed",
    correction="Add note about minimum 12 characters"
)

# 4. Use in future tasks
all_rules = rule.list()
```

---

## Best Practices

### Do This

- Start every session with `kg.build()` (incremental update)
- Review `omission_summary` on every `kg.retrieve()`
- Use compression levels strategically (0=debug, 3=quick scan)
- Store insights with `memory.set()` after discoveries
- Use `symbol.*` tools for code changes (not text manipulation)
- Create checkpoints at major milestones with `timeline.checkpoint()`
- Use specific task descriptions for better KG retrieval

### Avoid This

- Skipping `kg.build` - rebuild regularly as code changes
- Ignoring omission warnings - understand what wasn't loaded
- Text replacement for semantic operations - use `symbol.replace`
- Deep directory hierarchies - keep maximum 2-3 levels
- Generic task descriptions - be specific for better retrieval
- Assuming the KG is complete - always review available_expansions

---

## Documentation

### Feature Guides
- [Knowledge Graph Guide](claudedocs/knowledge-graph-guide.md) - Complete KG documentation with examples
- [Business Rules Guide](claudedocs/business-rules-guide.md) - Human-in-the-loop rule validation
- [Timeline Guide](claudedocs/timeline-guide.md) - Snapshots and safe rollback
- [Performance Benchmarks](claudedocs/performance-benchmarks.md) - KG build times and metrics

### Architecture
- [Project Map](.claude/map.md) - Complete architecture overview (70 tools)
- [CFA v2 Architecture](claudedocs/CFA_v2_Architecture.md) - Structure and contracts
- [Serena Integration](claudedocs/Serena_Integration.md) - LSP and semantic operations

---

## Architecture Principles

### 1. Knowledge First
Everything starts with building and querying the Knowledge Graph. Context drives decisions.

### 2. Transparency by Default
Every retrieval reports what was loaded, omitted, and available for expansion. No hidden context gaps.

### 3. Semantic Operations
Use LSP-powered symbol tools instead of text manipulation when possible. Enables refactoring at scale.

### 4. Persistent Learning
Store insights and rules in persistent memory and Knowledge Graph. Build on previous work.

### 5. Progressive Disclosure
Start with signatures and overviews. Expand to full details as needed. Manage token budgets effectively.

---

## Repository

GitHub: https://github.com/Rixmerz/context-first-arch

## Version

**v0.3.0** - Knowledge Graph & Omission Transparency (72 tools)

## License

MIT
