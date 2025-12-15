"""
Objective Manager Module

Manages end-to-end objectives with checkpoints and progress tracking.
Extracted from objective_define.py and objective_check.py as part of CFA migration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .models import Objective, Checkpoint, ObjectiveStatus
from .storage import OrchestrationStorage


class ObjectiveManager:
    """Manages objectives, checkpoints, and progress tracking."""

    def __init__(self, storage: OrchestrationStorage):
        """
        Initialize manager with storage.

        Args:
            storage: OrchestrationStorage instance for persistence
        """
        self.storage = storage

    def define(
        self,
        description: str,
        success_criteria: Optional[List[str]] = None,
        checkpoints: Optional[List[str]] = None,
        max_iterations: int = 10,
        project_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_activate: bool = True
    ) -> Dict[str, Any]:
        """
        Define a new objective with success criteria and checkpoints.

        Creates a trackable objective that can be worked on iteratively
        across multiple model interactions until completion.

        Args:
            description: Clear description of what needs to be accomplished
            success_criteria: List of specific criteria that define success
            checkpoints: Optional list of milestone descriptions
            max_iterations: Maximum iterations before objective fails (default 10)
            project_path: Optional CFA project path for context
            tags: Optional tags for organization
            auto_activate: Make this the active objective (default True)

        Returns:
            Dictionary with:
                - success: Operation success
                - objective_id: Unique identifier
                - objective: Full objective details
                - checkpoints_count: Number of checkpoints
                - is_active: Whether this is now active
        """
        try:
            objective_id = str(uuid.uuid4())

            # Generate checkpoints
            if checkpoints:
                checkpoint_list = [
                    Checkpoint(
                        id=f"checkpoint-{i}",
                        description=cp,
                        achieved=False
                    )
                    for i, cp in enumerate(checkpoints)
                ]
            elif success_criteria:
                checkpoint_list = [
                    Checkpoint(
                        id=f"criterion-{i}",
                        description=criterion,
                        achieved=False
                    )
                    for i, criterion in enumerate(success_criteria)
                ]
            else:
                checkpoint_list = self._generate_checkpoints(description)

            # Create objective
            objective = Objective(
                id=objective_id,
                description=description,
                success_criteria=success_criteria or [],
                checkpoints=checkpoint_list,
                status=ObjectiveStatus.ACTIVE,
                current_iteration=0,
                max_iterations=max_iterations,
                progress=0.0,
                created_at=datetime.now(),
                project_path=project_path,
                tags=tags or [],
                history=[]
            )

            # Persist objective
            self.storage.create_objective(objective)

            # Set as active if requested
            if auto_activate:
                self.storage.set_active_objective_id(objective_id)

            # Integrate with Task Tracker if project_path provided
            if project_path:
                self._start_task_tracking(objective, project_path)

            return {
                "success": True,
                "objective_id": objective_id,
                "objective": self._serialize_objective(objective),
                "checkpoints_count": len(checkpoint_list),
                "is_active": auto_activate,
                "message": f"Objective created: {description[:50]}{'...' if len(description) > 50 else ''}",
                "next_action": "Use objective.check to track progress or agent.spawn to start working"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to define objective: {str(e)}"
            }

    def check_progress(
        self,
        objective_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check progress on an objective.

        Args:
            objective_id: Optional specific objective ID (uses active if not provided)

        Returns:
            Dictionary with:
                - progress: Progress percentage
                - checkpoints: Checkpoint status
                - status: Objective status
                - estimated_remaining: Estimated iterations remaining
        """
        try:
            # Use active objective if not specified
            obj_id = objective_id or self.storage.get_active_objective_id()

            if not obj_id:
                return {
                    "success": False,
                    "error": "No objective specified and no active objective",
                    "hint": "Use objective.define to create an objective first"
                }

            objective = self.storage.get_objective(obj_id)

            if not objective:
                return {
                    "success": False,
                    "error": f"Objective {obj_id} not found"
                }

            # Calculate progress
            progress = self._calculate_progress(objective)
            objective.progress = progress

            # Update storage with new progress
            self.storage.update_objective(objective)

            # Get checkpoint status
            achieved = [cp for cp in objective.checkpoints if cp.achieved]
            pending = [cp for cp in objective.checkpoints if not cp.achieved]

            # Estimate remaining
            estimated_remaining = self._estimate_remaining_iterations(objective)

            return {
                "success": True,
                "objective_id": obj_id,
                "description": objective.description,
                "status": objective.status.value,
                "progress": round(progress, 1),
                "current_iteration": objective.current_iteration,
                "max_iterations": objective.max_iterations,
                "checkpoints": {
                    "total": len(objective.checkpoints),
                    "achieved": len(achieved),
                    "pending_count": len(pending),
                    "pending": [cp.description for cp in pending],
                    "achieved_list": [cp.description for cp in achieved]
                },
                "estimated_remaining_iterations": estimated_remaining,
                "is_complete": progress >= 100.0,
                "iterations_remaining": objective.max_iterations - objective.current_iteration
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Check failed: {str(e)}"
            }

    def achieve_checkpoint(
        self,
        checkpoint_id: str,
        objective_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a checkpoint as achieved.

        Args:
            checkpoint_id: ID of checkpoint to mark as achieved
            objective_id: Optional objective ID (uses active if not provided)
            notes: Optional notes about how it was achieved

        Returns:
            Dictionary with updated progress
        """
        try:
            obj_id = objective_id or self.storage.get_active_objective_id()

            if not obj_id:
                return {
                    "success": False,
                    "error": "No objective specified and no active objective"
                }

            objective = self.storage.get_objective(obj_id)

            if not objective:
                return {
                    "success": False,
                    "error": f"Objective {obj_id} not found"
                }

            # Find checkpoint
            checkpoint = None
            for cp in objective.checkpoints:
                if cp.id == checkpoint_id:
                    checkpoint = cp
                    break

            if not checkpoint:
                return {
                    "success": False,
                    "error": f"Checkpoint {checkpoint_id} not found",
                    "available_checkpoints": [
                        {"id": cp.id, "description": cp.description}
                        for cp in objective.checkpoints
                        if not cp.achieved
                    ]
                }

            if checkpoint.achieved:
                return {
                    "success": True,
                    "already_achieved": True,
                    "message": f"Checkpoint '{checkpoint.description}' was already achieved"
                }

            # Mark as achieved
            checkpoint.achieved = True
            checkpoint.achieved_at = datetime.now()
            checkpoint.notes = notes

            # Update progress
            progress = self._calculate_progress(objective)
            objective.progress = progress

            # Add to history
            objective.history.append({
                "event": "checkpoint_achieved",
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat(),
                "notes": notes
            })

            # Check if objective is complete
            if progress >= 100.0:
                objective.status = ObjectiveStatus.COMPLETED
                objective.completed_at = datetime.now()

            # Persist changes
            self.storage.update_objective(objective)

            # Integrate with Task Tracker if project_path provided
            if objective.project_path:
                self._update_task_tracking(objective, checkpoint)

            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "checkpoint_description": checkpoint.description,
                "progress": round(progress, 1),
                "objective_complete": progress >= 100.0,
                "remaining_checkpoints": [
                    cp.description for cp in objective.checkpoints
                    if not cp.achieved
                ],
                "message": f"Checkpoint achieved: {checkpoint.description}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to achieve checkpoint: {str(e)}"
            }

    def record_iteration(
        self,
        objective_id: Optional[str] = None,
        summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an iteration for the objective.

        Args:
            objective_id: Optional objective ID (uses active if not provided)
            summary: Optional summary of what was done in this iteration

        Returns:
            Dictionary with iteration count and status
        """
        try:
            obj_id = objective_id or self.storage.get_active_objective_id()

            if not obj_id:
                return {
                    "success": False,
                    "error": "Objective not found"
                }

            objective = self.storage.get_objective(obj_id)

            if not objective:
                return {
                    "success": False,
                    "error": "Objective not found"
                }

            # Increment iteration
            objective.current_iteration += 1

            # Add to history
            objective.history.append({
                "event": "iteration",
                "iteration": objective.current_iteration,
                "timestamp": datetime.now().isoformat(),
                "summary": summary
            })

            # Check if max iterations reached
            if objective.current_iteration >= objective.max_iterations:
                if objective.status == ObjectiveStatus.ACTIVE:
                    objective.status = ObjectiveStatus.FAILED
                    objective.completed_at = datetime.now()

            # Persist changes
            self.storage.update_objective(objective)

            return {
                "success": True,
                "current_iteration": objective.current_iteration,
                "max_iterations": objective.max_iterations,
                "iterations_remaining": objective.max_iterations - objective.current_iteration,
                "progress": objective.progress,
                "status": objective.status.value,
                "at_limit": objective.current_iteration >= objective.max_iterations
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to record iteration: {str(e)}"
            }

    def mark_failed(
        self,
        reason: str,
        objective_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark an objective as failed.

        Args:
            reason: Reason for failure
            objective_id: Optional objective ID (uses active if not provided)

        Returns:
            Dictionary with failure result
        """
        try:
            obj_id = objective_id or self.storage.get_active_objective_id()

            if not obj_id:
                return {
                    "success": False,
                    "error": "Objective not found"
                }

            objective = self.storage.get_objective(obj_id)

            if not objective:
                return {
                    "success": False,
                    "error": "Objective not found"
                }

            objective.status = ObjectiveStatus.FAILED
            objective.completed_at = datetime.now()

            objective.history.append({
                "event": "failed",
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            })

            # Persist changes
            self.storage.update_objective(objective)

            return {
                "success": True,
                "objective_id": obj_id,
                "status": "failed",
                "reason": reason,
                "progress_at_failure": objective.progress,
                "iterations_used": objective.current_iteration
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to mark objective as failed: {str(e)}"
            }

    def list_objectives(
        self,
        status: Optional[ObjectiveStatus] = None,
        include_completed: bool = False
    ) -> Dict[str, Any]:
        """
        List objectives with optional filtering.

        Args:
            status: Filter by status
            include_completed: Include completed objectives

        Returns:
            Dictionary with list of objectives and summary
        """
        try:
            filters = {}
            if status:
                filters["status"] = status

            objectives = self.storage.list_objectives(filters=filters)

            if not include_completed:
                objectives = [
                    o for o in objectives
                    if o.status not in [ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED]
                ]

            # Calculate summary (all objectives for stats)
            all_objectives = self.storage.list_objectives()
            summary = {
                "total": len(all_objectives),
                "active": sum(1 for o in all_objectives if o.status == ObjectiveStatus.ACTIVE),
                "completed": sum(1 for o in all_objectives if o.status == ObjectiveStatus.COMPLETED),
                "failed": sum(1 for o in all_objectives if o.status == ObjectiveStatus.FAILED)
            }

            return {
                "success": True,
                "objectives": [self._serialize_objective(o) for o in objectives],
                "summary": summary,
                "active_objective_id": self.storage.get_active_objective_id(),
                "filtered_count": len(objectives)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list objectives: {str(e)}"
            }

    def activate(
        self,
        objective_id: str
    ) -> Dict[str, Any]:
        """
        Set an objective as the active one.

        Args:
            objective_id: ID of objective to activate

        Returns:
            Dictionary with activation result
        """
        try:
            objective = self.storage.get_objective(objective_id)

            if not objective:
                return {
                    "success": False,
                    "error": f"Objective {objective_id} not found"
                }

            if objective.status != ObjectiveStatus.ACTIVE:
                return {
                    "success": False,
                    "error": f"Cannot activate {objective.status.value} objective"
                }

            self.storage.set_active_objective_id(objective_id)

            return {
                "success": True,
                "objective_id": objective_id,
                "description": objective.description,
                "message": f"Objective {objective_id[:8]} is now active"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Activation failed: {str(e)}"
            }

    def _generate_checkpoints(self, description: str) -> List[Checkpoint]:
        """
        Generate default checkpoints based on description.

        Args:
            description: Objective description

        Returns:
            List of generated checkpoints
        """
        # Basic checkpoints that apply to most objectives
        checkpoints = [
            Checkpoint(
                id="checkpoint-understand",
                description="Understand and clarify requirements",
                achieved=False
            ),
            Checkpoint(
                id="checkpoint-implement",
                description="Implement core functionality",
                achieved=False
            ),
            Checkpoint(
                id="checkpoint-validate",
                description="Validate implementation meets requirements",
                achieved=False
            )
        ]

        # Add task-specific checkpoints based on keywords
        lower_desc = description.lower()

        if "test" in lower_desc:
            checkpoints.insert(-1, Checkpoint(
                id="checkpoint-tests",
                description="Write and run tests",
                achieved=False
            ))

        if "refactor" in lower_desc:
            checkpoints.insert(1, Checkpoint(
                id="checkpoint-analyze",
                description="Analyze existing code for refactoring",
                achieved=False
            ))

        if "design" in lower_desc or "architect" in lower_desc:
            checkpoints.insert(1, Checkpoint(
                id="checkpoint-design",
                description="Create architectural design",
                achieved=False
            ))

        return checkpoints

    def _calculate_progress(self, objective: Objective) -> float:
        """
        Calculate objective progress based on achieved checkpoints.

        Args:
            objective: Objective to calculate progress for

        Returns:
            Progress percentage (0-100)
        """
        if not objective.checkpoints:
            return 0.0

        achieved = sum(1 for cp in objective.checkpoints if cp.achieved)
        return (achieved / len(objective.checkpoints)) * 100.0

    def _estimate_remaining_iterations(self, objective: Objective) -> int:
        """
        Estimate remaining iterations based on progress rate.

        Args:
            objective: Objective to estimate for

        Returns:
            Estimated remaining iterations
        """
        achieved = sum(1 for cp in objective.checkpoints if cp.achieved)
        pending = len(objective.checkpoints) - achieved

        if objective.current_iteration == 0 or achieved == 0:
            return pending

        # Progress per iteration
        rate = achieved / objective.current_iteration
        if rate == 0:
            return pending

        return max(1, int(pending / rate))

    def _serialize_objective(self, objective: Objective) -> Dict[str, Any]:
        """
        Serialize objective to dictionary for API responses.

        Args:
            objective: Objective to serialize

        Returns:
            Dictionary representation
        """
        return {
            "id": objective.id,
            "description": objective.description,
            "success_criteria": objective.success_criteria,
            "checkpoints": [
                {
                    "id": cp.id,
                    "description": cp.description,
                    "achieved": cp.achieved,
                    "achieved_at": cp.achieved_at.isoformat() if cp.achieved_at else None,
                    "notes": cp.notes
                }
                for cp in objective.checkpoints
            ],
            "status": objective.status.value,
            "current_iteration": objective.current_iteration,
            "max_iterations": objective.max_iterations,
            "progress": objective.progress,
            "created_at": objective.created_at.isoformat(),
            "completed_at": objective.completed_at.isoformat() if objective.completed_at else None,
            "project_path": objective.project_path,
            "tags": objective.tags,
            "history": objective.history
        }

    def _start_task_tracking(self, objective: Objective, project_path: str):
        """
        Start task tracking in CFA Task Tracker.

        Args:
            objective: Objective being started
            project_path: Path to CFA project
        """
        try:
            from pathlib import Path
            from src.core.task_tracker import start_task

            start_task(
                project_path=Path(project_path),
                goal=objective.description,
                next_steps=[cp.description for cp in objective.checkpoints]
            )
        except Exception:
            # Silently fail if Task Tracker unavailable
            pass

    def _update_task_tracking(self, objective: Objective, checkpoint: Checkpoint):
        """
        Update task tracking when checkpoint is achieved.

        Args:
            objective: Objective being worked on
            checkpoint: Checkpoint that was achieved
        """
        try:
            from pathlib import Path
            from src.core.task_tracker import update_task

            if objective.project_path:
                update_task(
                    project_path=Path(objective.project_path),
                    completed_items=[checkpoint.description]
                )
        except Exception:
            # Silently fail if Task Tracker unavailable
            pass
