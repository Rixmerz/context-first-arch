---
name: cfa-status
description: Show CFA project status dashboard - KG health, contracts, memory, safe points
icon: 📊
when: CFA projects
---

# CFA Project Status Dashboard

Display comprehensive status of Context-First Architecture components.

## Information Displayed

```
✅ CFA Project: [project-name]
├─ Knowledge Graph
│  ├─ Status: Built/Stale
│  ├─ Chunks: 234
│  ├─ Last build: 2 hours ago
│  └─ Coverage: 85%
│
├─ Contracts
│  ├─ Total: 12
│  ├─ Valid: 10
│  └─ Outdated: 2
│
├─ Memory
│  ├─ Learnings: 8
│  ├─ Tags: [gotcha, pattern, architecture]
│  └─ Last entry: 1 hour ago
│
├─ Safe Points
│  ├─ Total: 5
│  └─ Last: "Feature X complete"
│
├─ Decisions
│  ├─ Total: 12
│  └─ Recent: "Use async for IO"
│
└─ Issues Detected
   ├─ Functions without contracts: 3
   ├─ KG older than 1 day: true
   └─ Unresolved breaking changes: 0
```

## Usage

In Claude Code terminal:
```
/cfa-status
```

Or from code:
```python
from src.features.knowledge_graph import kg_status
from src.features.orchestration import SafePointManager
from src.features.memory import Memory

# Get all status info
status = {}
status["kg"] = kg_status(project_path=".")
status["safe_points"] = SafePointManager(".").list_all()
status["memory"] = Memory(".").search_all()
```

## Next Steps

Based on status output:
- **KG Stale?** → Run `kg.build(incremental=true)`
- **Contracts outdated?** → Run `contract.sync(impl_file="...")`
- **Memory getting big?** → Run `memory.consolidate()`
- **Safe points old?** → Clean up with `safe_point.delete()`

## See Also

- `kg.status` - Detailed Knowledge Graph metrics
- `safe_point.list` - List all checkpoints
- `memory.search` - Find specific learnings
- `rule.list` - View business rules
