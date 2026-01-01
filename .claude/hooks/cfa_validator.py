#!/usr/bin/env python3
"""
CFA Protocol Validator - Enforcement Hooks for Context-First Architecture v3

This module provides validation hooks that ensure agents follow the CFA protocol:
1. SessionStart: Force onboarding at session start
2. PreToolUse: Verify context was loaded before editing
3. PostToolUse: Remind to check breaking changes after edits
4. Stop: Verify documentation was updated before ending

Exit codes:
- 0: Success (allow action)
- 2: Block action (with reason in stderr)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# State file location
STATE_FILE = Path.home() / ".claude" / "cfa_session_state.json"


def load_state() -> Dict[str, Any]:
    """Load current session state."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {
        "session_id": None,
        "project_path": None,
        "onboarding_done": False,
        "kg_retrieve_done": False,
        "files_modified": [],
        "functions_modified": [],
        "kg_build_pending": False,
        "last_activity": None
    }


def save_state(state: Dict[str, Any]) -> None:
    """Save session state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_activity"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_cfa_project(project_path: str) -> bool:
    """Check if the current project uses CFA."""
    cfa_markers = [
        Path(project_path) / ".claude" / "settings.json",
        Path(project_path) / ".claude" / "knowledge_graph.db",
        Path(project_path) / "contracts",
    ]
    return any(m.exists() for m in cfa_markers)


def output_decision(decision: str, reason: str, system_message: str = None) -> None:
    """Output structured decision for Claude Code."""
    output = {
        "decision": decision,  # "approve" or "block"
        "reason": reason,
        "continue": True
    }
    if system_message:
        output["systemMessage"] = system_message
    print(json.dumps(output))


# ============================================================================
# HOOK: SessionStart
# ============================================================================

def handle_session_start(data: Dict[str, Any]) -> int:
    """
    Handle session start event.

    Checks if this is a CFA project and reminds about onboarding.
    """
    session_id = data.get("session_id", "unknown")
    cwd = data.get("cwd", os.getcwd())

    state = load_state()

    # Reset state for new session
    state["session_id"] = session_id
    state["project_path"] = cwd
    state["onboarding_done"] = False
    state["kg_retrieve_done"] = False
    state["files_modified"] = []
    state["functions_modified"] = []
    state["kg_build_pending"] = False

    save_state(state)

    if is_cfa_project(cwd):
        output_decision(
            "approve",
            "CFA project detected",
            """
## CFA Project Detected

This is a **Context-First Architecture v3** project. Follow this protocol:

1. **FIRST**: `workflow.onboard(project_path=".", show_instructions=true)`
2. **BEFORE EDITING**: `kg.retrieve(task="your task description")`
3. **AFTER FUNCTION CHANGES**: `contract.check_breaking(symbol="...")`
4. **BEFORE ENDING**: `kg.build(incremental=true)` + `memory.set` for learnings

Do NOT start coding without loading context first.
"""
        )

    return 0


# ============================================================================
# HOOK: PreToolUse (Edit/Write)
# ============================================================================

def handle_pre_edit(data: Dict[str, Any]) -> int:
    """
    Handle pre-edit validation.

    Blocks edits if kg.retrieve hasn't been called yet.
    """
    state = load_state()
    cwd = data.get("cwd", os.getcwd())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only enforce on CFA projects
    if not is_cfa_project(cwd):
        return 0

    # Skip validation for .claude/ internal files
    if ".claude/" in file_path or ".claude\\" in file_path:
        return 0

    # Check if context was loaded
    if not state.get("kg_retrieve_done", False):
        # First time - warn but allow (medium enforcement)
        if not state.get("edit_warning_shown", False):
            state["edit_warning_shown"] = True
            save_state(state)
            output_decision(
                "approve",
                "First edit without context - warning",
                """
## Warning: Editing Without Context

You're editing without calling `kg.retrieve` first.

**Recommended before continuing:**
```
kg.retrieve(project_path=".", task="describe your current task")
```

This ensures you understand existing patterns before making changes.
"""
            )
            return 0

    # Track modified file
    if file_path and file_path not in state.get("files_modified", []):
        state.setdefault("files_modified", []).append(file_path)
        state["kg_build_pending"] = True
        save_state(state)

    return 0


# ============================================================================
# HOOK: PostToolUse (Edit)
# ============================================================================

def handle_post_edit(data: Dict[str, Any]) -> int:
    """
    Handle post-edit actions.

    Reminds to check for breaking changes if function signatures might have changed.
    """
    state = load_state()
    cwd = data.get("cwd", os.getcwd())
    tool_input = data.get("tool_input", {})

    # Only enforce on CFA projects
    if not is_cfa_project(cwd):
        return 0

    # Check if edit might have modified function signatures
    old_string = tool_input.get("old_string", "")
    new_string = tool_input.get("new_string", "")
    file_path = tool_input.get("file_path", "")

    # Simple heuristic: function signature changed if def/function pattern differs
    function_keywords = ["def ", "async def ", "function ", "const ", "export function"]

    old_has_func = any(kw in old_string for kw in function_keywords)
    new_has_func = any(kw in new_string for kw in function_keywords)

    if old_has_func or new_has_func:
        # Extract function name (simple heuristic)
        import re
        func_pattern = r'(?:def|async def|function|const)\s+(\w+)'

        old_funcs = set(re.findall(func_pattern, old_string))
        new_funcs = set(re.findall(func_pattern, new_string))

        modified_funcs = old_funcs | new_funcs

        if modified_funcs:
            state.setdefault("functions_modified", []).extend(modified_funcs)
            save_state(state)

            output_decision(
                "approve",
                "Function signature may have changed",
                f"""
## Function Modified: Check for Breaking Changes

You modified function(s): **{', '.join(modified_funcs)}**

**Before marking task complete, run:**
```
contract.check_breaking(project_path=".", symbol="{list(modified_funcs)[0]}")
```

This ensures no callers are broken by your changes.
"""
            )

    return 0


# ============================================================================
# HOOK: Stop (Session End Check)
# ============================================================================

def handle_stop(data: Dict[str, Any]) -> int:
    """
    Handle session stop event.

    BLOCKS session if pending CFA actions exist.
    Exit code 2 = BLOCKED, user must complete actions first.
    """
    state = load_state()
    cwd = data.get("cwd", os.getcwd())

    # Only enforce on CFA projects
    if not is_cfa_project(cwd):
        return 0

    reminders = []
    blocking_issues = []

    # Check if files were modified but kg.build not run
    if state.get("kg_build_pending", False):
        files = state.get("files_modified", [])
        reminders.append(f"- `kg.build(incremental=true)` - {len(files)} file(s) modified")
        blocking_issues.append("kg_build_pending")

    # Check if functions were modified but not checked
    funcs = state.get("functions_modified", [])
    if funcs:
        reminders.append(f"- `contract.check_breaking` for: {', '.join(funcs[:3])}")
        blocking_issues.append("breaking_changes_unchecked")

    if reminders:
        # BLOCKING: Session cannot end until these are resolved
        output_decision(
            "block",  # 'block' decision
            "BLOCKED: Pending CFA actions must be completed",
            f"""
## ⛔ CFA SESSION BLOCKED - Pending Actions Required

You cannot end this session until you complete:

{chr(10).join(reminders)}

Also recommended:
- `memory.set(key="...", value="...", tags=["..."])` for any learnings
- `safe_point.create(task_summary="...")` if significant changes were made

**Resume the session and run these commands to unblock.**
"""
        )
        # Exit code 2 = BLOCK this action
        return 2

    # All checks passed - session can end
    output_decision(
        "approve",
        "CFA session checklist complete",
        "✅ Session closed cleanly - all CFA actions completed."
    )
    return 0


# ============================================================================
# HOOK: Track kg.retrieve calls
# ============================================================================

def handle_kg_retrieve(data: Dict[str, Any]) -> int:
    """Track when kg.retrieve is called."""
    state = load_state()
    state["kg_retrieve_done"] = True
    save_state(state)
    return 0


def handle_kg_build(data: Dict[str, Any]) -> int:
    """Track when kg.build is called."""
    state = load_state()
    state["kg_build_pending"] = False
    save_state(state)
    return 0


def handle_workflow_onboard(data: Dict[str, Any]) -> int:
    """Track when workflow.onboard is called."""
    state = load_state()
    state["onboarding_done"] = True
    state["kg_retrieve_done"] = True  # onboard includes context
    save_state(state)
    return 0


# ============================================================================
# MAIN DISPATCHER
# ============================================================================

def main():
    """Main entry point - dispatch based on event and tool."""
    try:
        # Read input from stdin
        data = json.load(sys.stdin)

        event = data.get("hook_event_name", "")
        tool_name = data.get("tool_name", "")

        # Dispatch to appropriate handler
        if event == "SessionStart":
            return handle_session_start(data)

        elif event == "PreToolUse":
            if tool_name in ("Edit", "Write"):
                return handle_pre_edit(data)
            elif tool_name == "mcp__cfa__kg_retrieve":
                return handle_kg_retrieve(data)
            elif tool_name == "mcp__cfa__kg_build":
                return handle_kg_build(data)
            elif tool_name == "mcp__cfa__workflow_onboard":
                return handle_workflow_onboard(data)

        elif event == "PostToolUse":
            if tool_name == "Edit":
                return handle_post_edit(data)

        elif event == "Stop":
            return handle_stop(data)

        return 0

    except Exception as e:
        # Non-blocking error - log but don't fail
        print(f"CFA Validator Error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
