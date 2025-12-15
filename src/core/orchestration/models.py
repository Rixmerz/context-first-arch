"""
Data models for Nova Agent Orchestration System.

Defines all enums and dataclasses used by the orchestration layer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ===== ENUMS =====

class ModelType(str, Enum):
    """Claude model types for task execution."""
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class TaskComplexity(str, Enum):
    """Task complexity levels for routing decisions."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ARCHITECTURAL = "architectural"


class InstanceStatus(str, Enum):
    """Status of spawned agent instances."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class ObjectiveStatus(str, Enum):
    """Status of objectives with checkpoints."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class LoopStatus(str, Enum):
    """Status of execution loops."""
    CONFIGURED = "configured"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


# ===== DATACLASSES =====

@dataclass
class TaskAnalysis:
    """Result of task complexity analysis."""
    complexity: TaskComplexity
    estimated_lines: int
    requires_planning: bool
    multi_file: bool
    task_type: str  # code, debug, test, refactor, design


@dataclass
class RoutingDecision:
    """Model routing decision with reasoning."""
    recommended_model: ModelType
    analysis: TaskAnalysis
    reasoning: str
    escalation_path: Optional[ModelType] = None
    confidence: float = 1.0


@dataclass
class Checkpoint:
    """Milestone within an objective."""
    id: str
    description: str
    achieved: bool = False
    achieved_at: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass
class AgentInstance:
    """Represents a spawned agent instance."""
    id: str
    model: ModelType
    task: str
    context: Optional[str]
    status: InstanceStatus
    spawned_at: datetime
    completed_at: Optional[datetime] = None
    timeout_ms: int = 120000
    max_tokens: int = 8000
    tags: List[str] = field(default_factory=list)
    project_path: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0


@dataclass
class Objective:
    """End-to-end goal with success criteria."""
    id: str
    description: str
    success_criteria: List[str]
    checkpoints: List[Checkpoint]
    status: ObjectiveStatus
    current_iteration: int = 0
    max_iterations: int = 10
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    project_path: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ExecutionLoop:
    """Iterative execution configuration."""
    id: str
    task: str
    condition_type: str  # objective_complete, all_checkpoints, manual
    max_iterations: int
    iteration_delay_ms: int
    enable_safe_points: bool
    escalation_threshold: int
    status: LoopStatus
    current_iteration: int = 0
    objective_id: Optional[str] = None
    project_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    completion_reason: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SafePoint:
    """Git commit safe point for rollback."""
    id: str
    commit_hash: str
    message: str
    timestamp: datetime
    files_changed: int
    project_path: str


@dataclass
class IterationRecord:
    """Record of a single loop iteration."""
    iteration_number: int
    timestamp: datetime
    summary: Optional[str] = None
    files_changed: Optional[List[str]] = None
    tokens_used: int = 0
    result: Optional[str] = None
    error: Optional[str] = None
