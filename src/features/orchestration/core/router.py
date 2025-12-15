"""
Task Routing Module

Analyzes task complexity and routes to optimal model (Haiku/Sonnet/Opus).
Extracted from agent_route.py as part of CFA migration.
"""

from typing import Optional, Tuple, List
from .models import TaskAnalysis, RoutingDecision, ModelType, TaskComplexity


# Complexity indicators for task analysis
COMPLEXITY_INDICATORS = {
    "architectural": [
        "architect", "system design", "microservice", "database schema",
        "api design", "infrastructure", "scalab", "design system"
    ],
    "complex": [
        "integrate", "migration", "e2e test", "performance", "security",
        "authentication", "authorization", "multiple component", "refactor",
        "debug", "complex"
    ],
    "medium": [
        "feature", "implement", "add", "create", "build", "update",
        "modify", "change", "component", "module"
    ],
    "simple": [
        "fix", "correct", "small", "minor", "tweak", "adjust"
    ],
    "trivial": [
        "typo", "readme", "comment", "rename", "format", "spacing"
    ]
}


# Model capabilities and specifications
MODEL_SPECS = {
    ModelType.HAIKU: {
        "strengths": ["fast", "routing", "simple tasks", "coordination"],
        "weaknesses": ["complex code", "architecture", "multi-file"],
        "cost_multiplier": 1.0
    },
    ModelType.SONNET: {
        "strengths": ["implementation", "debugging", "refactoring", "tests"],
        "weaknesses": ["deep architecture", "system design"],
        "cost_multiplier": 5.0
    },
    ModelType.OPUS: {
        "strengths": ["architecture", "planning", "complex reasoning", "design"],
        "weaknesses": ["simple tasks (overkill)"],
        "cost_multiplier": 15.0
    }
}


class TaskRouter:
    """Routes tasks to optimal models based on complexity analysis."""

    def analyze_task(
        self,
        task: str,
        context: Optional[str] = None
    ) -> TaskAnalysis:
        """
        Analyze task to determine complexity, scope, and characteristics.

        Args:
            task: Task description to analyze
            context: Optional context about project/codebase

        Returns:
            TaskAnalysis with complexity, estimated lines, and metadata
        """
        lower_task = task.lower()

        # Determine complexity and estimated lines
        complexity, estimated_lines = self._determine_complexity(lower_task)

        # Determine task type
        task_type = self._determine_task_type(lower_task)

        # Detect multi-file operations
        multi_file_indicators = [
            "across", "multiple", "all file", "component", "module",
            "several", "many file"
        ]
        multi_file = any(indicator in lower_task for indicator in multi_file_indicators)

        # Determine if planning is required
        requires_planning = (
            complexity in [TaskComplexity.COMPLEX, TaskComplexity.ARCHITECTURAL]
            or task_type == "design"
        )

        return TaskAnalysis(
            complexity=complexity,
            estimated_lines=estimated_lines,
            requires_planning=requires_planning,
            multi_file=multi_file,
            task_type=task_type
        )

    def route_task(
        self,
        task: str,
        context: Optional[str] = None,
        force_model: Optional[ModelType] = None
    ) -> RoutingDecision:
        """
        Route task to optimal model based on analysis.

        Args:
            task: Task description
            context: Optional context
            force_model: Optional model override

        Returns:
            RoutingDecision with recommended model and reasoning
        """
        # Handle forced model
        if force_model:
            return RoutingDecision(
                recommended_model=force_model,
                reasoning=f"Model forced to {force_model.value} by user request",
                confidence=1.0,
                alternative_models=[],
                analysis=TaskAnalysis(
                    complexity=TaskComplexity.MEDIUM,
                    estimated_lines=0,
                    requires_planning=False,
                    multi_file=False,
                    task_type="code"
                )
            )

        # Analyze task
        analysis = self.analyze_task(task, context)

        # Decide model
        recommended_model = self._decide_model(analysis)

        # Build reasoning
        reasoning = self._build_reasoning(analysis, recommended_model)

        # Determine alternatives (escalation path)
        alternative_models = self._get_alternative_models(recommended_model)

        # Calculate confidence (simplified)
        confidence = self._calculate_confidence(analysis, recommended_model)

        return RoutingDecision(
            recommended_model=recommended_model,
            reasoning=reasoning,
            confidence=confidence,
            alternative_models=alternative_models,
            analysis=analysis
        )

    def get_escalation_path(self, model: ModelType) -> Optional[ModelType]:
        """
        Get the next model in escalation hierarchy.

        Args:
            model: Current model

        Returns:
            Next model in escalation path, or None if at top
        """
        escalation_map = {
            ModelType.HAIKU: ModelType.SONNET,
            ModelType.SONNET: ModelType.OPUS,
            ModelType.OPUS: None
        }
        return escalation_map.get(model)

    def _determine_complexity(self, lower_task: str) -> Tuple[TaskComplexity, int]:
        """
        Determine task complexity level and estimated lines of code.

        Args:
            lower_task: Lowercased task description

        Returns:
            Tuple of (complexity level, estimated lines)
        """
        # Check complexity indicators in priority order
        for level_name in ["architectural", "complex", "medium", "simple", "trivial"]:
            indicators = COMPLEXITY_INDICATORS[level_name]
            if any(indicator in lower_task for indicator in indicators):
                complexity_map = {
                    "architectural": (TaskComplexity.ARCHITECTURAL, 500),
                    "complex": (TaskComplexity.COMPLEX, 300),
                    "medium": (TaskComplexity.MEDIUM, 100),
                    "simple": (TaskComplexity.SIMPLE, 30),
                    "trivial": (TaskComplexity.TRIVIAL, 5)
                }
                return complexity_map[level_name]

        # Default to medium
        return (TaskComplexity.MEDIUM, 100)

    def _determine_task_type(self, lower_task: str) -> str:
        """
        Determine the type of task (debug, test, refactor, design, code).

        Args:
            lower_task: Lowercased task description

        Returns:
            Task type string
        """
        if "debug" in lower_task or "fix bug" in lower_task:
            return "debug"
        elif "test" in lower_task or "spec" in lower_task:
            return "test"
        elif "refactor" in lower_task or "clean" in lower_task:
            return "refactor"
        elif "design" in lower_task or "plan" in lower_task or "architect" in lower_task:
            return "design"
        else:
            return "code"

    def _decide_model(self, analysis: TaskAnalysis) -> ModelType:
        """
        Decide which model should handle the task based on analysis.

        Args:
            analysis: Task analysis result

        Returns:
            Recommended model
        """
        # Architectural or design tasks → Opus
        if (analysis.complexity == TaskComplexity.ARCHITECTURAL
                or analysis.task_type == "design"):
            return ModelType.OPUS

        # Complex tasks or planning required → Sonnet
        if (analysis.complexity == TaskComplexity.COMPLEX
                or analysis.requires_planning):
            return ModelType.SONNET

        # Medium complexity → Sonnet (workhorse)
        if analysis.complexity == TaskComplexity.MEDIUM:
            return ModelType.SONNET

        # Simple but multi-file → Sonnet
        if (analysis.complexity == TaskComplexity.SIMPLE
                and analysis.multi_file):
            return ModelType.SONNET

        # Trivial or simple single-file → Haiku
        return ModelType.HAIKU

    def _build_reasoning(
        self,
        analysis: TaskAnalysis,
        model: ModelType
    ) -> str:
        """
        Generate human-readable reasoning for the routing decision.

        Args:
            analysis: Task analysis
            model: Selected model

        Returns:
            Reasoning string
        """
        reasons = [f"Complexity: {analysis.complexity.value}"]
        reasons.append(f"Estimated scope: ~{analysis.estimated_lines} lines")

        if analysis.multi_file:
            reasons.append("Multi-file changes detected")

        if analysis.requires_planning:
            reasons.append("Requires planning phase")

        model_roles = {
            ModelType.HAIKU: "Simple task - Haiku handles directly",
            ModelType.SONNET: "Implementation task - Sonnet executes",
            ModelType.OPUS: "Complex planning required - Opus architects"
        }
        reasons.append(model_roles.get(model, ""))

        return " | ".join(reasons)

    def _get_alternative_models(
        self,
        recommended_model: ModelType
    ) -> List[ModelType]:
        """
        Get list of alternative models (escalation path).

        Args:
            recommended_model: Primary recommendation

        Returns:
            List of alternative models
        """
        alternatives = []
        next_model = self.get_escalation_path(recommended_model)
        if next_model:
            alternatives.append(next_model)
        return alternatives

    def _calculate_confidence(
        self,
        analysis: TaskAnalysis,
        model: ModelType
    ) -> float:
        """
        Calculate confidence score for the routing decision.

        Args:
            analysis: Task analysis
            model: Selected model

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # High confidence for clear complexity indicators
        if analysis.complexity == TaskComplexity.ARCHITECTURAL:
            return 0.95 if model == ModelType.OPUS else 0.5
        elif analysis.complexity == TaskComplexity.TRIVIAL:
            return 0.95 if model == ModelType.HAIKU else 0.5
        elif analysis.complexity == TaskComplexity.COMPLEX:
            return 0.85 if model == ModelType.SONNET else 0.6
        else:
            # Medium confidence for ambiguous cases
            return 0.75
