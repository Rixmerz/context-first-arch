"""
Reflection tools for AI meta-cognition.

Provides structured thinking tools for:
- Information analysis
- Task adherence validation
- Completion assessment
- Change summarization
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from src.core.project import get_project_paths


def think_about_information(
    project_path: str,
    information: str,
    context: Optional[str] = None,
    questions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze collected information for a task.

    Provides a structured format for reflecting on gathered
    information before proceeding with implementation.

    Args:
        project_path: Path to the project root
        information: The information gathered so far
        context: Optional additional context
        questions: Specific questions to consider

    Returns:
        Dictionary with reflection structure
    """
    paths = get_project_paths(project_path)

    # Load current task context if available
    task_context = ""
    task_file = paths["claude_dir"] / "current-task.md"
    if task_file.exists():
        task_context = task_file.read_text(encoding="utf-8")

    # Load relevant contracts
    contracts = _load_relevant_contracts(paths["contracts_dir"], information)

    # Generate reflection prompts
    reflection_prompts = [
        "## Key Observations",
        "What are the most important findings from this information?",
        "",
        "## Relevance to Task",
        "How does this information relate to the current task?",
        "",
        "## Gaps Identified",
        "What information is still missing or unclear?",
        "",
        "## Contract Alignment",
        "Does this information align with existing contracts?",
        "",
        "## Next Steps",
        "What actions should be taken based on this analysis?",
    ]

    if questions:
        reflection_prompts.append("")
        reflection_prompts.append("## Specific Questions to Address")
        for q in questions:
            reflection_prompts.append(f"- {q}")

    return {
        "success": True,
        "project_path": str(paths["root"]),
        "information_summary": information[:500] + ("..." if len(information) > 500 else ""),
        "task_context": task_context[:300] if task_context else "No current task defined",
        "relevant_contracts": contracts,
        "reflection_template": "\n".join(reflection_prompts),
        "guidance": (
            "Use this template to structure your analysis of the collected information. "
            "Consider how the information aligns with contracts and task requirements."
        )
    }


def think_about_task(
    project_path: str,
    task_description: str,
    current_approach: str,
    concerns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate adherence to task requirements.

    Provides structured validation of current approach
    against task requirements and project contracts.

    Args:
        project_path: Path to the project root
        task_description: Description of the task
        current_approach: Current implementation approach
        concerns: Any specific concerns to address

    Returns:
        Dictionary with task adherence analysis
    """
    paths = get_project_paths(project_path)

    # Load contracts for validation
    contracts = _load_all_contracts(paths["contracts_dir"])

    # Load decisions
    decisions = ""
    decisions_file = paths["claude_dir"] / "decisions.md"
    if decisions_file.exists():
        decisions = decisions_file.read_text(encoding="utf-8")

    # Generate validation prompts
    validation_prompts = [
        "## Task Alignment Check",
        "",
        "### Original Requirements",
        f"Task: {task_description}",
        "",
        "### Current Approach",
        f"{current_approach}",
        "",
        "### Validation Points",
        "- [ ] Approach directly addresses stated requirements",
        "- [ ] No scope creep or unnecessary additions",
        "- [ ] Consistent with project architecture",
        "- [ ] Follows existing patterns and conventions",
        "- [ ] Respects contract boundaries",
        "",
        "### Contract Compliance",
        "Review each relevant contract for compliance.",
        "",
        "### Decision Alignment",
        "Verify approach aligns with architectural decisions.",
    ]

    if concerns:
        validation_prompts.append("")
        validation_prompts.append("### Concerns to Address")
        for concern in concerns:
            validation_prompts.append(f"- {concern}")

    return {
        "success": True,
        "project_path": str(paths["root"]),
        "task_summary": task_description[:200],
        "approach_summary": current_approach[:300],
        "contracts_to_check": [c["name"] for c in contracts],
        "has_decisions": bool(decisions),
        "validation_template": "\n".join(validation_prompts),
        "guidance": (
            "Use this checklist to validate your approach against task requirements. "
            "Flag any deviations or concerns before proceeding."
        )
    }


def think_about_completion(
    project_path: str,
    task_description: str,
    work_done: str,
    tests_passed: bool = False
) -> Dict[str, Any]:
    """
    Evaluate whether a task is truly complete.

    Provides structured assessment of task completion
    including validation against requirements.

    Args:
        project_path: Path to the project root
        task_description: Original task description
        work_done: Summary of work completed
        tests_passed: Whether tests have passed

    Returns:
        Dictionary with completion assessment
    """
    paths = get_project_paths(project_path)

    # Load current task if exists
    task_file = paths["claude_dir"] / "current-task.md"
    recorded_task = ""
    if task_file.exists():
        recorded_task = task_file.read_text(encoding="utf-8")

    # Generate completion checklist
    completion_checklist = [
        "## Completion Assessment",
        "",
        "### Requirements Fulfilled",
        "- [ ] All stated requirements are implemented",
        "- [ ] No partial implementations or TODOs",
        "- [ ] Edge cases have been considered",
        "",
        "### Quality Checks",
        f"- [{'x' if tests_passed else ' '}] Tests pass",
        "- [ ] Code follows project conventions",
        "- [ ] No obvious bugs or issues",
        "- [ ] Error handling is appropriate",
        "",
        "### Documentation",
        "- [ ] Code is self-documenting or commented",
        "- [ ] Any new APIs are documented",
        "- [ ] README updated if needed",
        "",
        "### Cleanup",
        "- [ ] No debug code left in",
        "- [ ] No unnecessary console.log/print statements",
        "- [ ] Files are properly formatted",
        "",
        "### Final Verification",
        "- [ ] Changes can be demonstrated",
        "- [ ] No unintended side effects",
    ]

    # Determine readiness
    is_likely_complete = tests_passed and len(work_done) > 50

    return {
        "success": True,
        "project_path": str(paths["root"]),
        "task_description": task_description[:200],
        "work_summary": work_done[:500],
        "tests_passed": tests_passed,
        "recorded_task": recorded_task[:300] if recorded_task else None,
        "completion_checklist": "\n".join(completion_checklist),
        "preliminary_assessment": (
            "Task appears ready for review" if is_likely_complete
            else "Task may need additional work - verify all checklist items"
        ),
        "guidance": (
            "Review this checklist carefully before marking the task complete. "
            "Ensure all items are checked or explicitly noted as not applicable."
        )
    }


def summarize_changes(
    project_path: str,
    changes: List[Dict[str, str]],
    task_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a structured summary of changes made.

    Creates a comprehensive summary suitable for
    commit messages, PR descriptions, or documentation.

    Args:
        project_path: Path to the project root
        changes: List of changes, each with 'file' and 'description'
        task_description: Optional task context

    Returns:
        Dictionary with formatted change summary
    """
    paths = get_project_paths(project_path)

    # Group changes by type
    grouped = {
        "added": [],
        "modified": [],
        "deleted": [],
        "other": []
    }

    for change in changes:
        change_type = change.get("type", "modified").lower()
        if change_type in grouped:
            grouped[change_type].append(change)
        else:
            grouped["other"].append(change)

    # Generate summary sections
    summary_parts = []

    if task_description:
        summary_parts.append(f"## Summary\n\n{task_description}")

    if grouped["added"]:
        summary_parts.append("## Added")
        for c in grouped["added"]:
            summary_parts.append(f"- `{c['file']}`: {c.get('description', 'New file')}")

    if grouped["modified"]:
        summary_parts.append("## Modified")
        for c in grouped["modified"]:
            summary_parts.append(f"- `{c['file']}`: {c.get('description', 'Updated')}")

    if grouped["deleted"]:
        summary_parts.append("## Deleted")
        for c in grouped["deleted"]:
            summary_parts.append(f"- `{c['file']}`: {c.get('description', 'Removed')}")

    if grouped["other"]:
        summary_parts.append("## Other Changes")
        for c in grouped["other"]:
            summary_parts.append(f"- `{c['file']}`: {c.get('description', '')}")

    # Generate commit message suggestion
    file_count = len(changes)
    primary_action = "Update" if grouped["modified"] else ("Add" if grouped["added"] else "Change")
    commit_suggestion = f"{primary_action} {file_count} file(s)"

    if task_description:
        # Extract first line for commit subject
        first_line = task_description.split("\n")[0][:50]
        commit_suggestion = first_line

    full_summary = "\n\n".join(summary_parts)

    # Optionally update decisions.md
    _append_to_decisions_if_significant(paths, changes, task_description)

    return {
        "success": True,
        "project_path": str(paths["root"]),
        "changes_count": len(changes),
        "files_added": len(grouped["added"]),
        "files_modified": len(grouped["modified"]),
        "files_deleted": len(grouped["deleted"]),
        "summary": full_summary,
        "commit_message_suggestion": commit_suggestion,
        "guidance": "Review the summary and use it for commit messages or documentation."
    }


def _load_relevant_contracts(contracts_dir: Path, context: str) -> List[Dict[str, str]]:
    """Load contracts that may be relevant to the context."""
    contracts = []

    if not contracts_dir.exists():
        return contracts

    context_lower = context.lower()

    for contract_file in contracts_dir.glob("*.contract.md"):
        try:
            name = contract_file.stem.replace(".contract", "")
            content = contract_file.read_text(encoding="utf-8")

            # Simple relevance check - contract name or keywords in context
            if name.lower() in context_lower or any(
                word in context_lower
                for word in name.lower().split("-")
            ):
                contracts.append({
                    "name": name,
                    "file": contract_file.name,
                    "preview": content[:200]
                })
        except Exception:
            continue

    return contracts[:5]  # Limit to top 5


def _load_all_contracts(contracts_dir: Path) -> List[Dict[str, str]]:
    """Load all contracts for validation."""
    contracts = []

    if not contracts_dir.exists():
        return contracts

    for contract_file in contracts_dir.glob("*.contract.md"):
        try:
            name = contract_file.stem.replace(".contract", "")
            contracts.append({
                "name": name,
                "file": contract_file.name
            })
        except Exception:
            continue

    return contracts


def _append_to_decisions_if_significant(
    paths: Dict[str, Path],
    changes: List[Dict[str, str]],
    task_description: Optional[str]
):
    """Append significant changes to decisions.md."""
    # Only record if significant (5+ files or architectural changes)
    if len(changes) < 5:
        return

    decisions_file = paths["claude_dir"] / "decisions.md"
    if not decisions_file.exists():
        return

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n\n## Auto-recorded: {timestamp}\n\n"

        if task_description:
            entry += f"**Task**: {task_description[:100]}\n\n"

        entry += f"**Files changed**: {len(changes)}\n"

        decisions_file.write_text(
            decisions_file.read_text() + entry,
            encoding="utf-8"
        )
    except Exception:
        pass  # Silent fail for auto-recording
