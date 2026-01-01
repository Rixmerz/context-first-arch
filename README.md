# Context-First Architecture v3

AI-assisted development framework with **intelligent context retrieval** and **omission transparency**.

## What Makes CFA v3 Special?

**Knowledge Graph** - Never wonder what your AI assistant knows or doesn't know. Every context retrieval shows:
- **What was loaded** and why
- **What was omitted** and why
- **What you can expand** next

Combined with **27 optimized MCP tools** across 9 categories, CFA v3 provides a complete AI-assisted development workflow.

---

## Quick Start

### 1. Install

```bash
pip install context-first-architecture
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
expanded = kg.context(
    chunk_id=result["available_expansions"][0]["chunk_id"],
    mode="expand"
)
```

---

## Advanced Features (NEW)

### 1. **Automatic Protocol Enforcement**
CFA now enforces best practices automatically:

```
SessionStart → Remind onboarding protocol
PreToolUse  → Warn if editing without context
PostToolUse → Remind about breaking changes
Stop        → Check pending documentation
```

**Files:** `.claude/hooks/cfa_validator.py` + Global hooks in `~/.claude/hooks/`

### 2. **Git Pre-commit Hook**
Automatic checks before every commit:
- ✅ Knowledge Graph exists and is fresh
- ✅ New feature files have contracts
- ✅ Code changes tracked

**File:** `.git/hooks/pre-commit`

### 3. **Project Status Dashboard** (`/cfa-status`)
Quick overview of CFA health:
```
Knowledge Graph: Status, chunks, age, coverage
Contracts: Total, valid, outdated
Memory: Learnings, tags, last update
Safe Points: Available checkpoints
Issues: Missing contracts, stale KG, breaking changes
```

**File:** `.claude/skills/cfa-status.md`

### 4. **Auto-audit Hook**
Detect architectural violations:
```
python3 .claude/hooks/cfa_audit.py .
```

Finds:
- Functions without contracts
- Undocumented changes
- Potential breaking changes
- Missing learnings in memory
- Stale Knowledge Graph

---

## Tools Overview (27 Total)

### Workflow (1 tool)
| Tool | Description |
|------|-------------|
| `workflow.onboard` | **[START HERE]** Load project context. Use `show_instructions=true` on first session. |

### Knowledge Graph (6 tools)
| Tool | Description |
|------|-------------|
| `kg.build` | Build/update Knowledge Graph. Use `update_map=true` to also update project map. |
| `kg.status` | Check graph health: chunks, edges, tokens, last build. |
| `kg.retrieve` | **[PRIMARY]** Task-aware context retrieval with omission transparency. |
| `kg.search` | BM25 keyword search across all chunks. |
| `kg.context` | Expand context. Modes: `expand`, `get`, `related`. |
| `kg.git` | Git operations. Operations: `history`, `blame`, `diff`. |

### Memory (5 tools)
| Tool | Description |
|------|-------------|
| `memory.set` | Store learnings across sessions. Tags: architecture, pattern, gotcha. |
| `memory.get` | Retrieve memory by exact key. |
| `memory.search` | Find memories by content or tags. |
| `memory.list` | List all stored memories. |
| `memory.delete` | Remove outdated memory. |

### Safe Points (3 tools)
| Tool | Description |
|------|-------------|
| `safe_point.create` | Create git checkpoint before risky changes. |
| `safe_point.rollback` | Revert to checkpoint. Use `mode="preview"` first. |
| `safe_point.list` | List available checkpoints. |

### Project (2 tools)
| Tool | Description |
|------|-------------|
| `project.init` | Create new CFA project structure. |
| `project.migrate` | Convert existing project to CFA. |

### Contract (4 tools)
| Tool | Description |
|------|-------------|
| `contract.create` | Generate contract from implementation code. |
| `contract.validate` | Check implementation matches contract. |
| `contract.sync` | Sync contract with code. Use `preview=true` to see diff first. |
| `contract.check_breaking` | **[CRITICAL]** Check for breaking changes after modifying function signatures. |

### Analysis (2 tools)
| Tool | Description |
|------|-------------|
| `analyze.structure` | With `target`: dependency analysis. Without: coupling analysis. |
| `analyze.change` | With `file_path`: impact analysis. Without: pattern detection. |

### Rules (3 tools)
| Tool | Description |
|------|-------------|
| `rule.interpret` | AI proposes business rules from code patterns. |
| `rule.confirm` | Confirm, correct, or reject rules. Supports batch via `rule_ids` array. |
| `rule.list` | List business rules. Filter by status, category, file. |

### Decision (1 tool)
| Tool | Description |
|------|-------------|
| `decision.add` | Record architectural decision with reasoning. |

---

## Core Concepts

### Knowledge Graph

Indexes your codebase as interconnected chunks with intelligent retrieval:

- **Smart Retrieval**: BM25 search + multi-hop graph traversal
- **Omission Transparency**: Always know what's NOT loaded and why
- **Progressive Disclosure**: Load signatures first, expand as needed
- **Compression Levels**: Control detail vs. tokens (0=full, 1=no_comments, 2=signatures)
- **Git Integration**: Historical analysis and blame tracking
- **Business Rules**: Capture tacit knowledge automatically

### Consolidated Tool Design

CFA v3 uses **mode/operation parameters** for related functionality:

```python
# Instead of separate tools:
# kg.expand(), kg.get(), kg.related()

# Use unified tool with mode:
kg.context(mode="expand", chunk_id="...")
kg.context(mode="get", chunk_ids=["..."])
kg.context(mode="related", chunk_id="...")

# Instead of:
# kg.history(), kg.blame(), kg.diff()

# Use:
kg.git(operation="history", file_path="...")
kg.git(operation="blame", file_path="...")
kg.git(operation="diff", commit_a="...", commit_b="...")
```

---

## Recommended Workflow

### Session Start

```python
# 1. Check Knowledge Graph status
kg.status(project_path=".")

# 2. Update if needed (with project map)
kg.build(project_path=".", incremental=True, update_map=True)

# 3. Load project context (with instructions on first session)
workflow.onboard(project_path=".", show_instructions=True)
```

### During Development

```python
# Get task-relevant context
result = kg.retrieve(
    project_path=".",
    task="implement user authentication",
    token_budget=10000
)

# Review omissions
print(result["omission_summary"])

# Expand specific chunks if needed
kg.context(
    project_path=".",
    mode="expand",
    chunk_id=result["available_expansions"][0]["chunk_id"]
)

# After modifying function signatures - CRITICAL!
contract.check_breaking(project_path=".", symbol="authenticate")
```

### Session End

```python
# Store learnings
memory.set(
    project_path=".",
    key="auth_gotcha",
    value="Token validation must check expiry first",
    tags=["auth", "gotcha"]
)

# Create checkpoint
safe_point.create(
    project_path=".",
    task_summary="Authentication feature complete"
)
```

---

## Project Structure

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
└── tests/                        # Test files
```

---

## Configuration

Create `.claude/settings.json` in your project:

```json
{
  "cfa_version": "3.0",
  "source_root": "src",
  "project_name": "My App",
  "languages": ["python", "typescript"],
  "knowledge_graph": {
    "auto_build": true,
    "incremental": true,
    "compression_default": 1,
    "max_chunk_size": 2000
  }
}
```

---

## Installation Options

```bash
# Installation
pip install context-first-architecture
```

---

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────┐
│  MCP Tools Layer (27 tools)     │
├─────────────────────────────────┤
│  Feature Modules (9 categories) │
├─────────────────────────────────┤
│  Core Components & Storage      │
└─────────────────────────────────┘
```

### Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| Workflow | 1 | Session initialization |
| Knowledge Graph | 6 | Context retrieval & search |
| Memory | 5 | Persistent learnings |
| Safe Points | 3 | Git checkpoints |
| Project | 2 | Setup & migration |
| Contract | 4 | Interface documentation |
| Analysis | 2 | Dependencies & patterns |
| Rules | 3 | Business logic capture |
| Decision | 1 | Architecture records |

---

## Best Practices

### Do This

- Start every session with `workflow.onboard()`
- Review `omission_summary` on every `kg.retrieve()`
- Use `contract.check_breaking()` after modifying function signatures
- Store insights with `memory.set()` after discoveries
- Create checkpoints with `safe_point.create()` before risky changes
- Use specific task descriptions for better KG retrieval

### Avoid This

- Skipping `kg.build` - rebuild regularly as code changes
- Ignoring omission warnings - understand what wasn't loaded
- Modifying function signatures without checking breaking changes
- Deep directory hierarchies - keep maximum 2-3 levels
- Generic task descriptions - be specific for better retrieval

---

## Version History

- **v0.4.0** - Optimized to 27 tools (consolidated from 41)
- **v0.3.0** - Knowledge Graph & Omission Transparency
- **v0.2.0** - CFA v2 Architecture
- **v0.1.0** - Initial release

## Repository

GitHub: https://github.com/Rixmerz/context-first-arch

## License

MIT
