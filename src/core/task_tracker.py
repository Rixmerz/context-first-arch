"""
Task tracking for Context-First Architecture.

Manages current-task.md for session state persistence.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


@dataclass
class Task:
    """Represents the current task state."""
    goal: str
    status: TaskStatus
    completed: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    context: str = ""
    started_at: Optional[datetime] = None


def load_task(project_path: str) -> Optional[Task]:
    """Load current task from project."""
    task_file = Path(project_path) / ".claude" / "current-task.md"

    if not task_file.exists():
        return None

    content = task_file.read_text()
    return _parse_task_md(content)


def save_task(project_path: str, task: Task) -> None:
    """Save task to current-task.md."""
    task_file = Path(project_path) / ".claude" / "current-task.md"
    content = _render_task_md(task)
    task_file.write_text(content)


def start_task(
    project_path: str,
    goal: str,
    next_steps: Optional[List[str]] = None,
    context: str = ""
) -> Task:
    """Start a new task."""
    task = Task(
        goal=goal,
        status=TaskStatus.IN_PROGRESS,
        completed=[],
        files_modified=[],
        blockers=[],
        next_steps=next_steps or [],
        context=context,
        started_at=datetime.now()
    )
    save_task(project_path, task)
    return task


def update_task(
    project_path: str,
    completed_items: Optional[List[str]] = None,
    files_modified: Optional[List[str]] = None,
    blockers: Optional[List[str]] = None,
    next_steps: Optional[List[str]] = None,
    context: Optional[str] = None,
    status: Optional[TaskStatus] = None
) -> Task:
    """Update current task with new progress."""
    task = load_task(project_path)

    if task is None:
        raise ValueError("No active task. Use start_task first.")

    if completed_items:
        task.completed.extend(completed_items)

    if files_modified:
        # Deduplicate while preserving order
        existing = set(task.files_modified)
        for f in files_modified:
            if f not in existing:
                task.files_modified.append(f)
                existing.add(f)

    if blockers is not None:
        task.blockers = blockers

    if next_steps is not None:
        task.next_steps = next_steps

    if context is not None:
        task.context = context

    if status is not None:
        task.status = status
    elif blockers:
        task.status = TaskStatus.BLOCKED
    elif not task.next_steps:
        task.status = TaskStatus.COMPLETED

    save_task(project_path, task)
    return task


def complete_task(project_path: str, summary: str = "") -> Task:
    """Mark current task as completed."""
    task = load_task(project_path)

    if task is None:
        raise ValueError("No active task to complete.")

    task.status = TaskStatus.COMPLETED
    task.blockers = []
    task.next_steps = []

    if summary:
        task.context = f"Completed: {summary}"

    save_task(project_path, task)
    return task


def _parse_task_md(content: str) -> Task:
    """Parse current-task.md content into Task object."""

    def extract_section(header: str) -> str:
        pattern = rf"## {header}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def extract_list(text: str) -> List[str]:
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- [x]"):
                items.append(line[5:].strip())
            elif line.startswith("- [ ]"):
                continue  # Skip uncompleted items for completed list
            elif line.startswith("- "):
                items.append(line[2:].strip())
            elif line.startswith("* "):
                items.append(line[2:].strip())
            elif line and line[0].isdigit() and ". " in line:
                items.append(line.split(". ", 1)[1].strip())
        return [i for i in items if i and i != "(none)"]

    goal = extract_section("Goal")
    status_str = extract_section("Status")
    completed_text = extract_section("What's Done")
    files_text = extract_section("Files Modified This Session")
    blockers_text = extract_section("Blockers")
    next_steps_text = extract_section("Next Steps")
    context_text = extract_section("Context for Next Session")

    # Parse status
    try:
        status = TaskStatus(status_str.upper().replace(" ", "_"))
    except ValueError:
        status = TaskStatus.NOT_STARTED

    # Parse completed items (including checked items)
    completed = []
    for line in completed_text.split("\n"):
        line = line.strip()
        if line.startswith("- [x]"):
            completed.append(line[5:].strip())
        elif line.startswith("- ") and not line.startswith("- [ ]"):
            completed.append(line[2:].strip())

    return Task(
        goal=goal,
        status=status,
        completed=completed,
        files_modified=extract_list(files_text),
        blockers=extract_list(blockers_text),
        next_steps=extract_list(next_steps_text),
        context=context_text if context_text != "(none)" else ""
    )


def _render_task_md(task: Task) -> str:
    """Render Task object to markdown."""

    def format_list(items: List[str], numbered: bool = False) -> str:
        if not items:
            return "(none)"
        if numbered:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        return "\n".join(f"- {item}" for item in items)

    def format_completed(items: List[str]) -> str:
        if not items:
            return "(none)"
        return "\n".join(f"- [x] {item}" for item in items)

    return f"""# Current Task

## Goal
{task.goal}

## Status
{task.status.value}

## What's Done
{format_completed(task.completed)}

## Files Modified This Session
{format_list(task.files_modified)}

## Blockers
{format_list(task.blockers) if task.blockers else "None"}

## Next Steps
{format_list(task.next_steps, numbered=True)}

## Context for Next Session
{task.context or "(none)"}
"""
