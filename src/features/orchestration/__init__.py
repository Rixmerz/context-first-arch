"""
Orchestration Feature - Safe Points

Git-based checkpoints for safe rollback during risky changes.

## Architecture (CFA v2 Pattern)

```
features/orchestration/
├── core/
│   ├── models.py           # SafePoint dataclass
│   ├── storage.py          # SQLite persistence
│   └── safe_points.py      # SafePointManager
└── tools/
    └── safe_point_*.py     # 3 MCP tools
```

## Usage

```python
from src.features.orchestration import SafePointManager

manager = SafePointManager(project_path)
manager.create(task_summary="Before refactoring")
# ... make changes ...
manager.rollback()  # Revert if needed
```

Note: Agent, Objective, Loop, and Config tools removed.
Use Claude Code's native TodoWrite and Task tools instead.
"""

from .core import SafePoint, OrchestrationStorage, SafePointManager

__all__ = [
    "SafePoint",
    "OrchestrationStorage",
    "SafePointManager",
]
