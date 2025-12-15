"""
Orchestration Feature - Nova Agent Orchestration

Multi-model AI task routing and execution system (Haiku/Sonnet/Opus).

## Architecture (CFA v2 Pattern)

```
features/orchestration/
├── core/
│   ├── models.py           # Enums and dataclasses
│   ├── storage.py          # SQLite persistence
│   ├── router.py           # Task routing logic
│   ├── executor.py         # Agent lifecycle
│   ├── objective_manager.py # Goal tracking
│   ├── loop_manager.py     # Iterative loops
│   └── safe_points.py      # Git rollback
├── tools/
│   ├── agent_*.py          # 3 agent tools
│   ├── objective_*.py      # 5 objective tools
│   ├── loop_*.py           # 4 loop tools
│   └── safe_point_*.py     # 3 safe point tools
└── tests/
```

## Usage

```python
from src.features.orchestration import TaskRouter, ModelType

# Route a task to optimal model
router = TaskRouter()
decision = router.route_task("Implement authentication")
print(decision.recommended_model)  # ModelType.SONNET
```
"""

from .core import (
    # Enums
    ModelType,
    TaskComplexity,
    InstanceStatus,
    ObjectiveStatus,
    LoopStatus,
    # Dataclasses
    TaskAnalysis,
    RoutingDecision,
    AgentInstance,
    Checkpoint,
    Objective,
    ExecutionLoop,
    SafePoint,
    IterationRecord,
    # Core classes
    OrchestrationStorage,
    TaskRouter,
    AgentExecutor,
    ObjectiveManager,
    LoopManager,
    SafePointManager,
)

__all__ = [
    # Enums
    "ModelType",
    "TaskComplexity",
    "InstanceStatus",
    "ObjectiveStatus",
    "LoopStatus",
    # Dataclasses
    "TaskAnalysis",
    "RoutingDecision",
    "AgentInstance",
    "Checkpoint",
    "Objective",
    "ExecutionLoop",
    "SafePoint",
    "IterationRecord",
    # Core classes
    "OrchestrationStorage",
    "TaskRouter",
    "AgentExecutor",
    "ObjectiveManager",
    "LoopManager",
    "SafePointManager",
]
