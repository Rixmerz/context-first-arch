"""
Loop Manager Module

Manages iterative execution loops that continue until conditions are met.
Extracted from loop_until.py as part of CFA migration.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from .models import ExecutionLoop, LoopStatus, Objective, ObjectiveStatus
from .storage import OrchestrationStorage
from .objective_manager import ObjectiveManager


class LoopManager:
    """Manages iterative execution loops with condition checking."""

    def __init__(
        self,
        storage: OrchestrationStorage,
        objective_manager: ObjectiveManager
    ):
        """
        Initialize manager with storage and objective manager.

        Args:
            storage: OrchestrationStorage instance for persistence
            objective_manager: ObjectiveManager for checking objective status
        """
        self.storage = storage
        self.objective_manager = objective_manager

    def configure(
        self,
        task: str,
        condition_type: str = "objective_complete",
        max_iterations: int = 10,
        iteration_delay_ms: int = 1000,
        enable_safe_points: bool = True,
        escalation_threshold: int = 5,
        project_path: Optional[str] = None,
        objective_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure a new iterative execution loop.

        Args:
            task: Task to work on iteratively
            condition_type: When to stop (objective_complete, all_checkpoints, manual)
            max_iterations: Maximum iterations before giving up
            iteration_delay_ms: Delay between iterations in milliseconds
            enable_safe_points: Create git commits after each iteration
            escalation_threshold: After this many iterations, escalate model
            project_path: Optional CFA project path
            objective_id: Optional objective to track

        Returns:
            Dictionary with:
                - success: Operation success
                - loop_id: Unique identifier
                - config: Loop configuration
                - instructions: How to execute the loop
        """
        try:
            loop_id = str(uuid.uuid4())

            # Validate condition type
            valid_conditions = ["objective_complete", "all_checkpoints", "manual"]
            if condition_type not in valid_conditions:
                return {
                    "success": False,
                    "error": f"Invalid condition_type: {condition_type}. Valid: {valid_conditions}"
                }

            # Get objective if needed
            obj_id = objective_id or self.storage.get_active_objective_id()
            objective = None
            if obj_id:
                objective = self.storage.get_objective(obj_id)

            if condition_type in ["objective_complete", "all_checkpoints"] and not objective:
                return {
                    "success": False,
                    "error": f"Condition type '{condition_type}' requires an objective. Use objective.define first.",
                    "hint": "Create an objective with objective.define or use condition_type='manual'"
                }

            # Create loop configuration
            execution_loop = ExecutionLoop(
                id=loop_id,
                task=task,
                condition_type=condition_type,
                max_iterations=max_iterations,
                iteration_delay_ms=iteration_delay_ms,
                enable_safe_points=enable_safe_points,
                escalation_threshold=escalation_threshold,
                project_path=project_path,
                objective_id=obj_id,
                status=LoopStatus.CONFIGURED,
                current_iteration=0,
                created_at=datetime.now(),
                history=[]
            )

            # Persist loop
            self.storage.create_loop(execution_loop)

            return {
                "success": True,
                "loop_id": loop_id,
                "config": self._serialize_loop(execution_loop),
                "objective": {
                    "id": obj_id,
                    "description": objective.description if objective else None,
                    "progress": objective.progress if objective else None
                } if objective else None,
                "instructions": {
                    "execution": (
                        f"Execute loop by calling loop.iterate with loop_id='{loop_id}'. "
                        f"Continue calling loop.iterate until loop.status shows completion."
                    ),
                    "workflow": [
                        f"1. Call loop.iterate('{loop_id}') to get next iteration context",
                        "2. Execute the task with appropriate model (use agent.route)",
                        "3. Update checkpoints with objective.achieve_checkpoint",
                        "4. Call loop.iterate again to continue or check completion",
                        f"5. Loop will stop when: {condition_type} or max {max_iterations} iterations"
                    ],
                    "safe_points": f"{'Enabled' if enable_safe_points else 'Disabled'} - commits after each iteration",
                    "escalation": f"Model escalation after iteration {escalation_threshold}"
                },
                "message": f"Loop configured: {task[:50]}{'...' if len(task) > 50 else ''}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create loop: {str(e)}"
            }

    def iterate(
        self,
        loop_id: str,
        iteration_result: Optional[str] = None,
        files_changed: Optional[List[str]] = None,
        tokens_used: int = 0
    ) -> Dict[str, Any]:
        """
        Advance to the next iteration of a loop.

        Args:
            loop_id: ID of the loop to iterate
            iteration_result: Optional summary of previous iteration
            files_changed: Optional list of files changed
            tokens_used: Tokens used in previous iteration

        Returns:
            Dictionary with:
                - success: Operation success
                - continue: Whether to continue looping
                - iteration: Current iteration number
                - context: Context for the next iteration
        """
        try:
            execution_loop = self.storage.get_loop(loop_id)

            if not execution_loop:
                return {
                    "success": False,
                    "error": f"Loop {loop_id} not found"
                }

            # Record previous iteration if there was one
            if execution_loop.current_iteration > 0 and iteration_result:
                execution_loop.history.append({
                    "iteration": execution_loop.current_iteration,
                    "result": iteration_result,
                    "files_changed": files_changed or [],
                    "tokens_used": tokens_used,
                    "timestamp": datetime.now().isoformat()
                })

            # Check condition
            should_continue, reason = self._check_condition(execution_loop)

            if not should_continue:
                execution_loop.status = (
                    LoopStatus.COMPLETED if "complete" in reason.lower()
                    else LoopStatus.STOPPED
                )
                execution_loop.completed_at = datetime.now()

                # Persist changes
                self.storage.update_loop(execution_loop)

                return {
                    "success": True,
                    "continue": False,
                    "loop_id": loop_id,
                    "reason": reason,
                    "status": execution_loop.status.value,
                    "total_iterations": execution_loop.current_iteration,
                    "total_tokens": sum(h.get("tokens_used", 0) for h in execution_loop.history),
                    "message": f"Loop completed: {reason}"
                }

            # Advance iteration
            execution_loop.current_iteration += 1
            execution_loop.status = LoopStatus.RUNNING

            # Check escalation
            should_escalate = execution_loop.current_iteration >= execution_loop.escalation_threshold
            current_model = "opus" if should_escalate else "sonnet"

            # Get objective progress if available
            obj_progress = None
            if execution_loop.objective_id:
                objective = self.storage.get_objective(execution_loop.objective_id)
                if objective:
                    obj_progress = {
                        "progress": objective.progress,
                        "pending_checkpoints": [
                            cp.description for cp in objective.checkpoints
                            if not cp.achieved
                        ]
                    }

            # Build iteration context
            iteration_context = self._build_iteration_context(execution_loop, obj_progress)

            # Persist changes
            self.storage.update_loop(execution_loop)

            return {
                "success": True,
                "continue": True,
                "loop_id": loop_id,
                "iteration": execution_loop.current_iteration,
                "max_iterations": execution_loop.max_iterations,
                "iterations_remaining": execution_loop.max_iterations - execution_loop.current_iteration,
                "recommended_model": current_model,
                "escalated": should_escalate,
                "task": execution_loop.task,
                "objective_progress": obj_progress,
                "context": {
                    "iteration_prompt": iteration_context,
                    "safe_point_enabled": execution_loop.enable_safe_points,
                    "previous_iterations": len(execution_loop.history)
                },
                "message": f"Iteration {execution_loop.current_iteration}/{execution_loop.max_iterations}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Iteration failed: {str(e)}"
            }

    def stop(
        self,
        loop_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stop a running loop.

        Args:
            loop_id: ID of the loop to stop
            reason: Optional reason for stopping

        Returns:
            Dictionary with stop result
        """
        try:
            execution_loop = self.storage.get_loop(loop_id)

            if not execution_loop:
                return {
                    "success": False,
                    "error": f"Loop {loop_id} not found"
                }

            execution_loop.status = LoopStatus.STOPPED
            execution_loop.completed_at = datetime.now()

            execution_loop.history.append({
                "event": "stopped",
                "timestamp": datetime.now().isoformat(),
                "reason": reason or "User requested"
            })

            # Persist changes
            self.storage.update_loop(execution_loop)

            return {
                "success": True,
                "loop_id": loop_id,
                "status": "stopped",
                "total_iterations": execution_loop.current_iteration,
                "reason": reason or "User requested",
                "message": f"Loop stopped after {execution_loop.current_iteration} iterations"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Stop failed: {str(e)}"
            }

    def get_status(
        self,
        loop_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get status of loops.

        Args:
            loop_id: Optional specific loop ID to query

        Returns:
            Dictionary with loop status or summary of all loops
        """
        try:
            # Specific loop query
            if loop_id:
                execution_loop = self.storage.get_loop(loop_id)
                if not execution_loop:
                    return {
                        "success": False,
                        "error": f"Loop {loop_id} not found"
                    }
                return {
                    "success": True,
                    "loop": self._serialize_loop(execution_loop)
                }

            # Return all loops summary
            all_loops = self.storage.list_loops()

            summary = {
                "total": len(all_loops),
                "configured": sum(1 for l in all_loops if l.status == LoopStatus.CONFIGURED),
                "running": sum(1 for l in all_loops if l.status == LoopStatus.RUNNING),
                "completed": sum(1 for l in all_loops if l.status == LoopStatus.COMPLETED),
                "stopped": sum(1 for l in all_loops if l.status == LoopStatus.STOPPED)
            }

            return {
                "success": True,
                "loops": [self._serialize_loop(l) for l in all_loops],
                "summary": summary
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Status check failed: {str(e)}"
            }

    def _check_condition(
        self,
        execution_loop: ExecutionLoop
    ) -> Tuple[bool, str]:
        """
        Check if loop should continue.

        Args:
            execution_loop: Loop to check

        Returns:
            Tuple of (should_continue, reason)
        """
        # Check max iterations
        if execution_loop.current_iteration >= execution_loop.max_iterations:
            return (False, "Max iterations reached")

        condition_type = execution_loop.condition_type

        if condition_type == "manual":
            return (True, "Manual mode - continue until stopped")

        obj_id = execution_loop.objective_id
        if not obj_id:
            return (True, "No objective - continue")

        objective = self.storage.get_objective(obj_id)
        if not objective:
            return (True, "No objective - continue")

        if condition_type == "objective_complete":
            if objective.status == ObjectiveStatus.COMPLETED:
                return (False, "Objective completed")
            return (True, "Objective in progress")

        if condition_type == "all_checkpoints":
            pending = [cp for cp in objective.checkpoints if not cp.achieved]
            if not pending:
                return (False, "All checkpoints achieved")
            return (True, f"{len(pending)} checkpoints remaining")

        return (True, "Unknown condition - continue")

    def _should_escalate(self, execution_loop: ExecutionLoop) -> bool:
        """
        Check if model should be escalated based on iteration count.

        Args:
            execution_loop: Loop to check

        Returns:
            True if should escalate
        """
        return execution_loop.current_iteration >= execution_loop.escalation_threshold

    def _build_iteration_context(
        self,
        execution_loop: ExecutionLoop,
        obj_progress: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build context string for the current iteration.

        Args:
            execution_loop: Current loop
            obj_progress: Optional objective progress info

        Returns:
            Context string for iteration prompt
        """
        parts = [f"Task: {execution_loop.task}"]
        parts.append(f"\nIteration: {execution_loop.current_iteration}/{execution_loop.max_iterations}")

        if obj_progress:
            parts.append(f"\nProgress: {obj_progress['progress']:.1f}%")
            if obj_progress['pending_checkpoints']:
                parts.append("\nPending checkpoints:")
                for i, cp in enumerate(obj_progress['pending_checkpoints'][:5]):
                    parts.append(f"  {i+1}. {cp}")

        if execution_loop.current_iteration >= execution_loop.escalation_threshold:
            parts.append("\n[ESCALATED] This task has been escalated for deeper analysis.")

        return "\n".join(parts)

    def _serialize_loop(self, execution_loop: ExecutionLoop) -> Dict[str, Any]:
        """
        Serialize loop to dictionary for API responses.

        Args:
            execution_loop: Loop to serialize

        Returns:
            Dictionary representation
        """
        return {
            "id": execution_loop.id,
            "task": execution_loop.task,
            "condition_type": execution_loop.condition_type,
            "max_iterations": execution_loop.max_iterations,
            "iteration_delay_ms": execution_loop.iteration_delay_ms,
            "enable_safe_points": execution_loop.enable_safe_points,
            "escalation_threshold": execution_loop.escalation_threshold,
            "project_path": execution_loop.project_path,
            "objective_id": execution_loop.objective_id,
            "status": execution_loop.status.value,
            "current_iteration": execution_loop.current_iteration,
            "created_at": execution_loop.created_at.isoformat(),
            "completed_at": execution_loop.completed_at.isoformat() if execution_loop.completed_at else None,
            "history": execution_loop.history
        }
