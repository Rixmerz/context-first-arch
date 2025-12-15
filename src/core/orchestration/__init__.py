"""
Orchestration Module

Nova Agent Orchestration System - CFA compliant architecture.
Multi-model AI task routing and execution (Haiku/Sonnet/Opus).

This module provides:
- Task routing based on complexity analysis
- Agent instance lifecycle management
- Objective tracking with checkpoints
- Iterative execution loops
- Git-based safe points for rollback

Architecture:
- Tool Layer (thin wrappers) → Core Layer (business logic) → Storage Layer (SQLite)
"""

# Models
from .models import (
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
    IterationRecord
)

# Storage
from .storage import OrchestrationStorage

# Core managers
from .router import TaskRouter
from .executor import AgentExecutor
from .objective_manager import ObjectiveManager
from .loop_manager import LoopManager
from .safe_points import SafePointManager


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


__version__ = "3.0.0"
__author__ = "Context-First Architecture"
__description__ = "Nova Agent Orchestration - CFA v3 compliant"
