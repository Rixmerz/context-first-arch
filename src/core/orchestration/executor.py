"""
Agent Executor Module

Manages agent instance lifecycle: spawning, status tracking, termination.
Extracted from agent_spawn.py and agent_status.py as part of CFA migration.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from .models import AgentInstance, ModelType, InstanceStatus
from .storage import OrchestrationStorage


# Model to agent type mapping for Claude Code Task Tool
MODEL_TO_AGENT = {
    ModelType.HAIKU: "general-purpose",
    ModelType.SONNET: "python-expert",
    ModelType.OPUS: "system-architect"
}


class AgentExecutor:
    """Manages agent instance lifecycle and execution."""

    def __init__(self, storage: OrchestrationStorage):
        """
        Initialize executor with storage.

        Args:
            storage: OrchestrationStorage instance for persistence
        """
        self.storage = storage

    def spawn(
        self,
        model: ModelType,
        task: str,
        context: Optional[str] = None,
        project_path: Optional[str] = None,
        timeout_ms: int = 120000,
        max_tokens: int = 8000,
        background: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Spawn a new agent instance to execute a task.

        Creates an instance record and prepares spawn configuration
        for Claude Code's Task Tool.

        Args:
            model: Model type (HAIKU, SONNET, OPUS)
            task: Task description for the agent
            context: Optional context to provide
            project_path: Optional CFA project path
            timeout_ms: Timeout in milliseconds
            max_tokens: Maximum tokens for response
            background: Run in background mode
            tags: Optional tags for tracking

        Returns:
            Dictionary with:
                - success: Operation success
                - instance_id: Unique identifier
                - spawn_config: Config for Task Tool
                - instance: Instance record
                - task_tool_call: Direct Task tool parameters
        """
        try:
            # Validate model
            if model not in MODEL_TO_AGENT:
                return {
                    "success": False,
                    "error": f"Invalid model: {model.value}. Valid models: haiku, sonnet, opus"
                }

            # Generate instance ID
            instance_id = str(uuid.uuid4())

            # Create instance record
            instance = AgentInstance(
                id=instance_id,
                model=model,
                task=task,
                context=context,
                status=InstanceStatus.PENDING,
                spawned_at=datetime.now(),
                timeout_ms=timeout_ms,
                max_tokens=max_tokens,
                tags=tags or [],
                project_path=project_path
            )

            # Persist instance
            self.storage.create_instance(instance)

            # Build spawn configuration
            spawn_config = self._build_spawn_config(instance, background)

            return {
                "success": True,
                "instance_id": instance_id,
                "spawn_config": spawn_config,
                "instance": {
                    "id": instance.id,
                    "model": instance.model.value,
                    "task": instance.task,
                    "status": instance.status.value,
                    "spawned_at": instance.spawned_at.isoformat(),
                    "tags": instance.tags
                },
                "status": instance.status.value,
                "message": f"Instance {instance_id[:8]} prepared for {model.value} model",
                "task_tool_call": {
                    "tool": "Task",
                    "parameters": spawn_config
                },
                "instructions": (
                    f"To spawn this instance, use the Task tool with:\n"
                    f"  - prompt: {spawn_config['prompt'][:100]}...\n"
                    f"  - subagent_type: {MODEL_TO_AGENT[model]}\n"
                    f"  - model: {model.value}\n"
                    f"  - run_in_background: {background}"
                )
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Spawn preparation failed: {str(e)}"
            }

    def get_status(
        self,
        instance_id: Optional[str] = None,
        model: Optional[ModelType] = None,
        status: Optional[InstanceStatus] = None,
        tags: Optional[List[str]] = None,
        include_completed: bool = False
    ) -> Dict[str, Any]:
        """
        Get status of agent instances with optional filtering.

        Args:
            instance_id: Specific instance to query
            model: Filter by model type
            status: Filter by status
            tags: Filter by tags (any match)
            include_completed: Include completed/failed instances

        Returns:
            Dictionary with:
                - success: Operation success
                - instances: List of matching instances
                - summary: Aggregated statistics
                - token_usage: Token usage by model
        """
        try:
            # Query specific instance
            if instance_id:
                instance = self.storage.get_instance(instance_id)
                if instance:
                    return {
                        "success": True,
                        "instance": self._serialize_instance(instance),
                        "found": True
                    }
                else:
                    return {
                        "success": True,
                        "instance": None,
                        "found": False,
                        "message": f"Instance {instance_id} not found"
                    }

            # List instances with filters
            filters = {}
            if model:
                filters["model"] = model
            if status:
                filters["status"] = status
            if tags:
                filters["tags"] = tags

            instances = self.storage.list_instances(filters=filters)

            # Filter out completed if requested
            if not include_completed:
                instances = [
                    i for i in instances
                    if i.status not in [InstanceStatus.COMPLETED, InstanceStatus.FAILED]
                ]

            # Calculate statistics
            stats = self._calculate_statistics(instances)

            # Calculate token usage (all instances for accurate tracking)
            all_instances = self.storage.list_instances()
            token_usage = self._calculate_token_usage(all_instances)

            # Serialize instances
            serialized_instances = [
                self._serialize_instance(i) for i in instances
            ]

            return {
                "success": True,
                "instances": serialized_instances,
                "summary": stats,
                "token_usage": token_usage,
                "all_instances_count": len(all_instances),
                "filters_applied": {
                    "model": model.value if model else None,
                    "status": status.value if status else None,
                    "tags": tags,
                    "include_completed": include_completed
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get status: {str(e)}"
            }

    def terminate(
        self,
        instance_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Terminate a running agent instance.

        Args:
            instance_id: ID of instance to terminate
            reason: Optional reason for termination

        Returns:
            Dictionary with termination result
        """
        try:
            instance = self.storage.get_instance(instance_id)

            if not instance:
                return {
                    "success": False,
                    "error": f"Instance {instance_id} not found"
                }

            # Check if already terminated
            if instance.status in [
                InstanceStatus.COMPLETED,
                InstanceStatus.FAILED,
                InstanceStatus.TERMINATED
            ]:
                return {
                    "success": False,
                    "error": f"Instance {instance_id} is already {instance.status.value}"
                }

            # Update to terminated status
            instance.status = InstanceStatus.TERMINATED
            instance.completed_at = datetime.now()
            instance.error = reason or "User requested termination"

            self.storage.update_instance(instance)

            return {
                "success": True,
                "instance_id": instance_id,
                "status": "terminated",
                "message": f"Instance {instance_id[:8]} terminated",
                "reason": reason or "User requested"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Termination failed: {str(e)}"
            }

    def mark_completed(
        self,
        instance_id: str,
        result: str,
        tokens_used: int = 0
    ) -> bool:
        """
        Mark an instance as completed with results.

        Args:
            instance_id: ID of instance
            result: Result/output from the agent
            tokens_used: Tokens consumed

        Returns:
            True if successful, False otherwise
        """
        try:
            instance = self.storage.get_instance(instance_id)
            if not instance:
                return False

            instance.status = InstanceStatus.COMPLETED
            instance.completed_at = datetime.now()
            instance.result = result
            instance.tokens_used = tokens_used

            self.storage.update_instance(instance)
            return True

        except Exception:
            return False

    def mark_failed(
        self,
        instance_id: str,
        error: str
    ) -> bool:
        """
        Mark an instance as failed with error.

        Args:
            instance_id: ID of instance
            error: Error message/description

        Returns:
            True if successful, False otherwise
        """
        try:
            instance = self.storage.get_instance(instance_id)
            if not instance:
                return False

            instance.status = InstanceStatus.FAILED
            instance.completed_at = datetime.now()
            instance.error = error

            self.storage.update_instance(instance)
            return True

        except Exception:
            return False

    def clear_completed(self) -> Dict[str, Any]:
        """
        Remove completed, failed, and terminated instances from storage.

        Returns:
            Dictionary with count of cleared instances
        """
        try:
            all_instances = self.storage.list_instances()

            terminal_statuses = [
                InstanceStatus.COMPLETED,
                InstanceStatus.FAILED,
                InstanceStatus.TERMINATED
            ]

            cleared_count = 0
            for instance in all_instances:
                if instance.status in terminal_statuses:
                    # Note: OrchestrationStorage doesn't have delete_instance yet
                    # This would need to be added or we keep all instances for history
                    cleared_count += 1

            remaining = len(all_instances) - cleared_count

            return {
                "success": True,
                "cleared_count": cleared_count,
                "remaining_count": remaining,
                "message": f"Cleared {cleared_count} completed/failed instances"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Clear failed: {str(e)}"
            }

    def _build_spawn_config(
        self,
        instance: AgentInstance,
        background: bool
    ) -> Dict[str, str]:
        """
        Build spawn configuration for Claude Code Task Tool.

        Args:
            instance: Agent instance record
            background: Run in background mode

        Returns:
            Configuration dictionary for Task tool
        """
        # Build full prompt with context
        full_prompt = instance.task
        if instance.context:
            full_prompt = f"Context:\n{instance.context}\n\nTask:\n{instance.task}"

        # Get agent type mapping
        agent_type = MODEL_TO_AGENT[instance.model]

        # Create short description
        description = instance.task[:50] + "..." if len(instance.task) > 50 else instance.task

        return {
            "prompt": full_prompt,
            "subagent_type": agent_type,
            "model": instance.model.value,
            "description": description,
            "run_in_background": str(background).lower()
        }

    def _serialize_instance(self, instance: AgentInstance) -> Dict[str, Any]:
        """
        Serialize instance to dictionary for API responses.

        Args:
            instance: Agent instance

        Returns:
            Dictionary representation
        """
        return {
            "id": instance.id,
            "model": instance.model.value,
            "task": instance.task,
            "context": instance.context,
            "status": instance.status.value,
            "spawned_at": instance.spawned_at.isoformat(),
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "timeout_ms": instance.timeout_ms,
            "max_tokens": instance.max_tokens,
            "tags": instance.tags,
            "project_path": instance.project_path,
            "result": instance.result,
            "error": instance.error,
            "tokens_used": instance.tokens_used
        }

    def _calculate_statistics(
        self,
        instances: List[AgentInstance]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate statistics for instances.

        Args:
            instances: List of instances

        Returns:
            Statistics dictionary
        """
        stats = {
            "total": len(instances),
            "by_model": {},
            "by_status": {}
        }

        for instance in instances:
            model_key = instance.model.value
            status_key = instance.status.value

            stats["by_model"][model_key] = stats["by_model"].get(model_key, 0) + 1
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

        return stats

    def _calculate_token_usage(
        self,
        instances: List[AgentInstance]
    ) -> Dict[str, Any]:
        """
        Calculate token usage across all instances.

        Args:
            instances: List of all instances

        Returns:
            Token usage dictionary
        """
        token_usage = {
            "total": 0,
            "by_model": {
                "haiku": 0,
                "sonnet": 0,
                "opus": 0
            }
        }

        for instance in instances:
            tokens = instance.tokens_used
            token_usage["total"] += tokens

            model_key = instance.model.value
            if model_key in token_usage["by_model"]:
                token_usage["by_model"][model_key] += tokens

        return token_usage
