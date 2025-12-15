# Nova Agent Orchestration - Architecture Documentation

## Overview

Nova is the multi-model AI orchestration system integrated into Context-First Architecture (CFA) v3. It enables intelligent task routing and execution across Haiku, Sonnet, and Opus models, with support for iterative loops, objective tracking, and git-based safe points.

**Migration Date**: December 15, 2025
**CFA Version**: v3
**Architecture Pattern**: CFA v2 compliant (1 file = 1 MCP function)

## Architecture Layers

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Tool Layer (MCP Tools)                                 │
│  /src/mcp_server/tools/                                │
│  - 15 individual tool files (thin wrappers)            │
│  - Validation & error handling                         │
│  - Manager caching for performance                     │
└─────────────────────────────────────────────────────────┘
                        ↓ delegates to
┌─────────────────────────────────────────────────────────┐
│  Core Layer (Business Logic)                           │
│  /src/core/orchestration/                              │
│  - 6 manager classes                                   │
│  - Task routing & complexity analysis                  │
│  - Agent lifecycle management                          │
│  - Objective & loop orchestration                      │
└─────────────────────────────────────────────────────────┘
                        ↓ persists to
┌─────────────────────────────────────────────────────────┐
│  Storage Layer (SQLite)                                │
│  .claude/orchestration.db                              │
│  - 5 tables with 7 indexes                            │
│  - Transaction-safe operations                         │
│  - ACID guarantees                                     │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/
├── core/
│   └── orchestration/              # Core business logic (1,750 lines)
│       ├── __init__.py            # Public API exports
│       ├── models.py              # Dataclasses + Enums (166 lines)
│       ├── storage.py             # SQLite persistence (626 lines)
│       ├── router.py              # Task routing (310 lines)
│       ├── executor.py            # Agent lifecycle (450 lines)
│       ├── objective_manager.py   # Goal tracking (716 lines)
│       ├── loop_manager.py        # Iterative loops (470 lines)
│       └── safe_points.py         # Git rollback (470 lines)
│
└── mcp_server/
    └── tools/                      # MCP tool layer (750 lines)
        ├── agent_route.py          # Task routing wrapper (127 lines)
        ├── agent_spawn.py          # Agent spawning wrapper (115 lines)
        ├── agent_status.py         # Status query wrapper (115 lines)
        ├── objective_define.py     # Define objectives (101 lines)
        ├── objective_check.py      # Check progress (72 lines)
        ├── objective_achieve_checkpoint.py  # Mark checkpoints (69 lines)
        ├── objective_record_iteration.py    # Record iterations (68 lines)
        ├── objective_fail.py       # Mark failure (67 lines)
        ├── loop_configure.py       # Configure loops (83 lines)
        ├── loop_iterate.py         # Advance iterations (77 lines)
        ├── loop_stop.py            # Stop loops (69 lines)
        ├── loop_status.py          # Loop status (67 lines)
        ├── safe_point_create.py    # Create safe points (88 lines)
        ├── safe_point_rollback.py  # Rollback git (76 lines)
        └── safe_point_list.py      # List safe points (61 lines)
```

**Total**: ~2,500 lines (1,750 core + 750 tools)

## Core Layer Components

### 1. models.py - Data Structures

**Enums (5)**:
- `ModelType`: haiku, sonnet, opus
- `TaskComplexity`: trivial, simple, medium, complex, architectural
- `InstanceStatus`: pending, running, completed, failed, terminated
- `ObjectiveStatus`: active, completed, failed
- `LoopStatus`: pending, running, paused, completed, failed

**Dataclasses (8)**:
- `TaskAnalysis`: Complexity analysis result
- `RoutingDecision`: Model selection with reasoning
- `AgentInstance`: Spawned model instance
- `Checkpoint`: Milestone within objective
- `Objective`: End-to-end goal with checkpoints
- `ExecutionLoop`: Iterative execution config
- `SafePoint`: Git commit restore point
- `IterationRecord`: Loop iteration history

### 2. storage.py - Persistence Layer

**Database**: `.claude/orchestration.db` (SQLite)

**Tables (5)**:

```sql
agent_instances
  - id, model, task, status, spawned_at, completed_at
  - timeout_ms, max_tokens, tags, project_path
  - result, error, tokens_used

objectives
  - id, description, checkpoints (JSON), status
  - current_checkpoint_index, max_iterations, created_at
  - project_path, tags, progress_percentage

execution_loops
  - id, task, condition_type, status, current_iteration
  - max_iterations, iteration_delay_ms, enable_safe_points
  - escalation_threshold, objective_id, project_path

safe_points
  - id, commit_hash, message, timestamp
  - files_changed (JSON), project_path

active_state
  - key, value (singleton state: active_objective_id)
```

**Indexes (7)**:
- agent_instances: status, model, project_path
- objectives: status, project_path
- execution_loops: status, objective_id
- safe_points: project_path

### 3. router.py - Task Routing

**Purpose**: Analyze task complexity and route to optimal model.

**Key Components**:
- `COMPLEXITY_INDICATORS`: Keyword patterns for complexity analysis
- `MODEL_SPECS`: Model capabilities (Haiku: 8K, Sonnet: 16K, Opus: 32K)
- `TaskRouter.analyze_task()`: Complexity scoring
- `TaskRouter.route_task()`: Model selection with reasoning
- `TaskRouter.get_escalation_path()`: Model upgrade path

**Complexity Scoring**:
```python
trivial: 0.0-0.2     → Haiku
simple: 0.2-0.4      → Haiku
medium: 0.4-0.6      → Sonnet
complex: 0.6-0.8     → Sonnet/Opus
architectural: 0.8+  → Opus
```

### 4. executor.py - Agent Lifecycle

**Purpose**: Spawn and manage model instances.

**Key Components**:
- `MODEL_TO_AGENT`: Maps models to Task tool agent types
- `AgentExecutor.spawn()`: Create instance + configure Task tool
- `AgentExecutor.get_status()`: Query instances with filters
- `AgentExecutor.terminate()`: Stop running instance
- `AgentExecutor.mark_completed()`: Record success
- `AgentExecutor.mark_failed()`: Record failure

**Instance Lifecycle**:
```
pending → running → completed
                  ↘ failed
                  ↘ terminated
```

### 5. objective_manager.py - Goal Tracking

**Purpose**: Track end-to-end objectives with checkpoints and progress.

**Key Components**:
- `ObjectiveManager.define()`: Create objective with checkpoints
- `ObjectiveManager.check_progress()`: Calculate progress %
- `ObjectiveManager.achieve_checkpoint()`: Mark milestone complete
- `ObjectiveManager.record_iteration()`: Track iteration attempts
- `ObjectiveManager.mark_failed()`: Mark objective as failed

**CFA Integration**:
```python
# Task Tracker integration
from src.core.task_tracker import start_task, update_task

# On define():
start_task(
    project_path=project_path,
    goal=description,
    next_steps=[cp.description for cp in checkpoints]
)

# On achieve_checkpoint():
update_task(
    project_path=project_path,
    completed_items=[checkpoint.description]
)
```

### 6. loop_manager.py - Iterative Execution

**Purpose**: Configure and manage iterative loops until condition met.

**Key Components**:
- `LoopManager.configure()`: Setup loop config
- `LoopManager.iterate()`: Advance to next iteration
- `LoopManager.stop()`: Stop loop early
- `LoopManager.get_status()`: Query loop state

**Stop Conditions**:
- `objective_complete`: Stop when active objective completed
- `all_checkpoints`: Stop when all checkpoints achieved
- `manual`: Stop on explicit call to loop.stop

**Escalation**:
After `escalation_threshold` iterations, suggest model upgrade (Haiku → Sonnet → Opus).

### 7. safe_points.py - Git Rollback

**Purpose**: Create git commits as restore points.

**Key Components**:
- `SafePointManager.create()`: Git commit + record
- `SafePointManager.rollback()`: Git reset to safe point
- `SafePointManager.list_safe_points()`: List available safe points

**Memory Store Integration**:
```python
from src.core.memory_store import MemoryStore

# On create():
memory.set(
    key=f"safe_point_{safe_point_id}",
    value=f"Safe point created: {task_summary}",
    tags=["nova", "safe_point", "git"]
)
```

## Tool Layer (MCP Interface)

### Pattern: 1 File = 1 Function (CFA v2)

Every MCP tool follows this structure:

```python
"""
MCP Tool: <name>
<description>
Part of Nova Agent Orchestration System (CFA v3).
"""

from typing import Any, Dict, Optional
from pathlib import Path
from src.core.orchestration import <Manager>, OrchestrationStorage

# Cache global para reutilizar managers
_managers: Dict[str, <Manager>] = {}

def _get_manager(project_path: Optional[str]) -> <Manager>:
    key = project_path or "default"
    if key not in _managers:
        path = Path(project_path) if project_path else Path.cwd()
        storage = OrchestrationStorage(path)
        _managers[key] = <Manager>(storage)
    return _managers[key]

async def <tool_name>(...) -> Dict[str, Any]:
    """[Docstring]"""
    try:
        # Validation
        if not required_param:
            return {"success": False, "error": "..."}

        # Get manager (cached)
        manager = _get_manager(project_path)

        # Delegate to core
        result = manager.method(...)

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Tool Categories

**Agent Tools (3)**:
- `agent.route`: Analyze task complexity → recommend model
- `agent.spawn`: Spawn model instance via Task tool
- `agent.status`: Query instance status with filters

**Objective Tools (5)**:
- `objective.define`: Create objective with checkpoints
- `objective.check`: Check progress on active objective
- `objective.achieve_checkpoint`: Mark checkpoint complete
- `objective.record_iteration`: Record iteration attempt
- `objective.fail`: Mark objective as failed

**Loop Tools (4)**:
- `loop.configure`: Setup iterative execution loop
- `loop.iterate`: Advance to next iteration
- `loop.stop`: Stop loop early
- `loop.status`: Query loop state

**Safe Point Tools (3)**:
- `safe_point.create`: Create git commit as restore point
- `safe_point.rollback`: Reset to previous safe point
- `safe_point.list`: List available safe points

## Usage Examples

### 1. Basic Task Routing

```python
# Analyze and route a task
result = await agent_route(
    task="Implement user authentication with JWT",
    context="Express.js REST API"
)

# Response:
{
    "decision": "sonnet",
    "confidence": 0.85,
    "reasoning": "Medium complexity task requiring authentication knowledge...",
    "alternative": "opus",
    "complexity_score": 0.62
}
```

### 2. Spawn Agent Instance

```python
# Spawn Sonnet to implement feature
result = await agent_spawn(
    model="sonnet",
    task="Implement JWT authentication middleware",
    context="Express.js project with existing user model",
    project_path="/path/to/project",
    timeout=300000,  # 5 minutes
    tags=["auth", "feature"]
)

# Response:
{
    "success": True,
    "instance_id": "inst_abc123",
    "model": "sonnet",
    "status": "pending",
    "message": "Agent instance spawned and ready"
}
```

### 3. Define Objective with Checkpoints

```python
# Create objective for feature implementation
result = await objective_define(
    description="Implement complete user authentication system",
    success_criteria=[
        "JWT tokens generated and validated",
        "Refresh token rotation implemented",
        "Password hashing with bcrypt",
        "Tests passing with >90% coverage"
    ],
    checkpoints=[
        "JWT middleware implemented",
        "Login/logout endpoints created",
        "Password hashing added",
        "Tests written and passing"
    ],
    project_path="/path/to/project"
)

# Response:
{
    "success": True,
    "objective_id": "obj_xyz789",
    "checkpoints_generated": 4,
    "progress_percentage": 0.0,
    "status": "active"
}
```

### 4. Configure Iterative Loop

```python
# Setup loop for incremental implementation
result = await loop_configure(
    task="Implement authentication system incrementally",
    condition_type="all_checkpoints",
    max_iterations=10,
    enable_safe_points=True,
    escalation_threshold=5,
    objective_id="obj_xyz789"
)

# Response:
{
    "success": True,
    "loop_id": "loop_def456",
    "status": "pending",
    "instructions": "Use loop.iterate to advance iterations..."
}
```

### 5. Create Safe Point

```python
# Create git safe point before risky operation
result = await safe_point_create(
    project_path="/path/to/project",
    task_summary="JWT middleware implemented and tested",
    files_changed=["src/middleware/auth.js", "tests/auth.test.js"]
)

# Response:
{
    "success": True,
    "safe_point_id": "sp_ghi789",
    "commit_hash": "abc123def456",
    "message": "[Nova] JWT middleware implemented and tested"
}
```

## CFA Integrations

### Task Tracker

Nova objectives automatically sync with Task Tracker:

```python
# When objective is defined
start_task(
    project_path=project_path,
    goal=objective.description,
    next_steps=[cp.description for cp in checkpoints]
)

# When checkpoint is achieved
update_task(
    project_path=project_path,
    completed_items=[checkpoint.description]
)
```

### Memory Store

Safe points are archived in Memory Store:

```python
memory.set(
    key=f"safe_point_{safe_point_id}",
    value=f"Safe point: {task_summary}",
    tags=["nova", "safe_point", "git"]
)
```

### Knowledge Graph (Future)

Planned integration to track code changes by agent instance:

```python
# Track which agent modified which code chunks
kg.link_agent_to_chunks(
    agent_instance_id=instance.id,
    chunks_modified=changed_chunks
)
```

## Database Schema Details

### agent_instances Table

```sql
CREATE TABLE agent_instances (
    id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    task TEXT NOT NULL,
    context TEXT,
    status TEXT NOT NULL,
    spawned_at TEXT NOT NULL,
    completed_at TEXT,
    timeout_ms INTEGER DEFAULT 120000,
    max_tokens INTEGER DEFAULT 8000,
    tags TEXT,  -- JSON array
    project_path TEXT,
    result TEXT,
    error TEXT,
    tokens_used INTEGER DEFAULT 0
)
```

### objectives Table

```sql
CREATE TABLE objectives (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    checkpoints TEXT NOT NULL,  -- JSON array
    status TEXT NOT NULL,
    current_checkpoint_index INTEGER DEFAULT 0,
    max_iterations INTEGER DEFAULT 10,
    created_at TEXT NOT NULL,
    project_path TEXT,
    tags TEXT,  -- JSON array
    progress_percentage REAL DEFAULT 0.0
)
```

### execution_loops Table

```sql
CREATE TABLE execution_loops (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    status TEXT NOT NULL,
    current_iteration INTEGER DEFAULT 0,
    max_iterations INTEGER DEFAULT 10,
    iteration_delay_ms INTEGER DEFAULT 1000,
    enable_safe_points INTEGER DEFAULT 1,
    escalation_threshold INTEGER DEFAULT 5,
    objective_id TEXT,
    project_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### safe_points Table

```sql
CREATE TABLE safe_points (
    id TEXT PRIMARY KEY,
    commit_hash TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    files_changed TEXT,  -- JSON array
    project_path TEXT NOT NULL
)
```

### active_state Table

```sql
CREATE TABLE active_state (
    key TEXT PRIMARY KEY,
    value TEXT
)
-- Stores: active_objective_id
```

## Design Decisions

### Why CFA v2 Pattern?

**Before**: 7 tool files with multiple functions each (1,858 lines)
**After**: 15 individual tool files (2,500 lines total)

**Benefits**:
1. **Clarity**: One file = one responsibility
2. **Discoverability**: Easy to find specific functionality
3. **Consistency**: Matches existing CFA patterns (memory_*, symbol_*, file_*, kg_*)
4. **Maintainability**: Changes isolated to single files
5. **Testability**: Each tool can be tested independently

### Why SQLite?

**Before**: In-memory state (lost on restart)
**After**: SQLite persistence (durable across sessions)

**Benefits**:
1. **Durability**: Survives process restarts
2. **ACID**: Transaction-safe operations
3. **Zero Config**: No external database required
4. **Queryable**: SQL for complex queries
5. **Portable**: Single .db file

### Why Three Layers?

**Tool Layer** (MCP interface):
- Validation & error handling
- Manager caching for performance
- Thin wrappers (50-115 lines each)

**Core Layer** (business logic):
- All orchestration logic
- Model routing algorithms
- State management
- CFA integrations

**Storage Layer** (persistence):
- Database operations
- Transaction management
- CRUD operations

**Benefits**:
1. **Separation of Concerns**: Each layer has single responsibility
2. **Testability**: Can test core logic without MCP
3. **Reusability**: Core can be used outside MCP context
4. **Maintainability**: Changes localized to appropriate layer

## Performance Considerations

### Manager Caching

Each tool uses a global cache to reuse manager instances:

```python
_managers: Dict[str, <Manager>] = {}

def _get_manager(project_path: Optional[str]) -> <Manager>:
    key = project_path or "default"
    if key not in _managers:
        # Create new manager
        _managers[key] = <Manager>(storage)
    return _managers[key]
```

**Benefits**:
- Single storage connection per project
- Reduced database overhead
- Faster subsequent calls

### Database Indexes

7 indexes ensure fast queries:
- `idx_agent_status`: Filter by status
- `idx_agent_model`: Filter by model
- `idx_agent_project`: Filter by project
- `idx_objective_status`: Active objectives
- `idx_objective_project`: Project objectives
- `idx_loop_status`: Running loops
- `idx_safe_point_project`: Project safe points

### Transaction Management

Storage uses context manager for safe transactions:

```python
@contextmanager
def _get_connection(self):
    conn = sqlite3.connect(str(self.db_path))
    try:
        yield conn
    finally:
        conn.close()
```

## Testing Strategy

### Unit Tests

Test each core component in isolation:

```python
# tests/core/orchestration/test_router.py
def test_route_simple_task():
    router = TaskRouter()
    decision = router.route_task("Fix typo in README")
    assert decision.recommended_model == ModelType.HAIKU
    assert decision.complexity_score < 0.3

# tests/core/orchestration/test_storage.py
def test_create_instance(tmp_path):
    storage = OrchestrationStorage(tmp_path)
    instance = AgentInstance(...)
    storage.create_instance(instance)
    retrieved = storage.get_instance(instance.id)
    assert retrieved.id == instance.id
```

### Integration Tests

Test complete workflows:

```python
# tests/integration/test_nova_workflow.py
async def test_complete_workflow():
    # Route → Spawn → Check status
    route_result = await agent_route("Implement auth")
    assert route_result["decision"] == "sonnet"

    spawn_result = await agent_spawn(
        model=route_result["decision"],
        task="Implement auth"
    )
    assert spawn_result["success"] is True

    status_result = await agent_status(
        instance_id=spawn_result["instance_id"]
    )
    assert status_result["status"] == "pending"
```

## Migration Notes

**Files Created (18)**:
- 8 core files (models, storage, router, executor, objective_manager, loop_manager, safe_points, __init__)
- 10 new tool files (objective_*, loop_*, safe_point_*)

**Files Refactored (5)**:
- agent_route.py, agent_spawn.py, agent_status.py
- objective_define.py, objective_check.py

**Files Deleted (2)**:
- loop_until.py (replaced by loop_*.py)
- prehook_commit.py (replaced by safe_point_*.py)

**Files Modified (2)**:
- tools/__init__.py (updated imports and __all__)
- server.py (updated schemas and TOOL_MAP)

**Backward Compatibility**:
- All 15 MCP function names preserved
- No breaking changes for existing users
- Database migration automatic on first run

## Future Enhancements

### Phase 2: Real Agent Spawning

Currently Nova uses mock spawning. Future:
- Actual Task tool invocation
- Background execution support
- Real-time status updates
- Output capture and streaming

### Phase 3: Metrics & Observability

- Token usage tracking per instance
- Success/failure rates by model
- Average completion times
- Cost tracking (if API-based)

### Phase 4: Knowledge Graph Integration

- Track code changes by agent instance
- Link objectives to modified chunks
- Visualize agent impact on codebase
- Query "which agent modified this code?"

### Phase 5: Multi-Agent Collaboration

- Multiple agents working in parallel
- Agent-to-agent communication
- Shared objective coordination
- Conflict resolution strategies

## Troubleshooting

### Database Issues

**Problem**: Database locked
**Solution**: Ensure no other process accessing `.claude/orchestration.db`

**Problem**: Corrupted database
**Solution**: Delete `.claude/orchestration.db` (will be recreated)

### Tool Errors

**Problem**: "Manager not found"
**Solution**: Clear manager cache, restart MCP server

**Problem**: "Safe point creation failed"
**Solution**: Verify git repo, check file permissions

### Performance Issues

**Problem**: Slow tool calls
**Solution**: Check database indexes, verify manager caching

**Problem**: High memory usage
**Solution**: Clear completed instances, limit safe point history

## References

- [CFA Architecture Guide](./cfa-architecture.md)
- [Nova Migration Notes](./nova-migration-notes.md)
- [MCP Server Design Philosophy](../README.md#mcp-design-philosophy)
- [Task Tracker Integration](./task-tracker-guide.md)
- [Memory Store Guide](./memory-store-guide.md)
