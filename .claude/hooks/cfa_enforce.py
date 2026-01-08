#!/usr/bin/env python3
"""
CFA v4 Enforcement Hook - Blocks edits without onboarding.

Hooks:
- PreToolUse (Edit|Write): Blocks if cfa.onboard not called
- PreToolUse (mcp__cfa4__cfa_onboard): Marks session as onboarded

Exit codes:
- 0: Allow action
- 2: Block action (reason in stderr)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# State file - tracks if onboarding was done this session
STATE_FILE = Path.home() / ".claude" / "cfa_session_state.json"


def load_state():
    """Load session state."""
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            # Check if state is from current day (simple session detection)
            if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return data
    except:
        pass
    return {"onboarded": False, "date": datetime.now().strftime("%Y-%m-%d")}


def save_state(state):
    """Save session state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["date"] = datetime.now().strftime("%Y-%m-%d")
    STATE_FILE.write_text(json.dumps(state))


def is_cfa_project(cwd):
    """Check if current directory is a CFA project."""
    markers = [
        Path(cwd) / ".claude" / "settings.json",
        Path(cwd) / ".claude" / "map.md",
    ]
    return any(m.exists() for m in markers)


def main():
    try:
        data = json.load(sys.stdin)
    except:
        sys.exit(0)  # No input, allow
    
    tool_name = data.get("tool_name", "")
    cwd = data.get("cwd", os.getcwd())
    
    # Only enforce on CFA projects
    if not is_cfa_project(cwd):
        sys.exit(0)
    
    state = load_state()
    
    # Track cfa.onboard calls
    if tool_name == "mcp__cfa4__cfa_onboard":
        state["onboarded"] = True
        state["project"] = cwd
        save_state(state)
        sys.exit(0)
    
    # Block Edit/Write if not onboarded
    if tool_name in ("Edit", "Write"):
        # Skip .claude/ internal files
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if ".claude/" in file_path or ".claude\\" in file_path:
            sys.exit(0)
        
        if not state.get("onboarded"):
            # OUTPUT JSON for clear feedback
            output = {
                "decision": "block",
                "reason": "CFA Protocol: Must call cfa.onboard(project_path=\".\") before editing code"
            }
            print(json.dumps(output))
            sys.exit(2)  # BLOCK
    
    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
