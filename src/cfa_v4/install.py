#!/usr/bin/env python3
"""
CFA v4 Installer - Sets up enforcement hooks globally.

Usage:
    cfa4-install          # Install hooks to ~/.claude/
    cfa4-install --remove # Remove CFA hooks
"""

import json
import shutil
import sys
from pathlib import Path

HOOK_CODE = '''#!/usr/bin/env python3
"""
CFA v4 Enforcement Hook - Blocks edits without onboarding.

Exit codes:
- 0: Allow action
- 2: Block action
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

STATE_FILE = Path.home() / ".claude" / "cfa_session_state.json"


def load_state():
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                return data
    except:
        pass
    return {"onboarded": False, "date": datetime.now().strftime("%Y-%m-%d")}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["date"] = datetime.now().strftime("%Y-%m-%d")
    STATE_FILE.write_text(json.dumps(state))


def is_cfa_project(cwd):
    markers = [
        Path(cwd) / ".claude" / "settings.json",
        Path(cwd) / ".claude" / "map.md",
    ]
    return any(m.exists() for m in markers)


def main():
    try:
        data = json.load(sys.stdin)
    except:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    cwd = data.get("cwd", os.getcwd())

    if not is_cfa_project(cwd):
        sys.exit(0)

    state = load_state()

    # Track onboard calls
    if tool_name == "mcp__cfa4__cfa_onboard":
        state["onboarded"] = True
        state["project"] = cwd
        save_state(state)
        sys.exit(0)

    # Block Edit/Write without onboard
    if tool_name in ("Edit", "Write"):
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if ".claude/" in file_path or ".claude\\\\" in file_path:
            sys.exit(0)

        if not state.get("onboarded"):
            print(json.dumps({
                "decision": "block",
                "reason": "CFA Protocol: Must call cfa.onboard(project_path=\\".\\") before editing code"
            }))
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
'''

HOOKS_CONFIG = {
    "PreToolUse": [
        {
            "matcher": "Edit|Write",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/cfa_enforce.py",
                    "timeout": 5
                }
            ]
        },
        {
            "matcher": "mcp__cfa4__cfa_onboard",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 ~/.claude/hooks/cfa_enforce.py",
                    "timeout": 5
                }
            ]
        }
    ]
}


def install():
    """Install CFA v4 hooks globally."""
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_file = claude_dir / "settings.json"
    hook_file = hooks_dir / "cfa_enforce.py"

    print("CFA v4 Installer")
    print("=" * 40)

    # Create directories
    hooks_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created {hooks_dir}")

    # Write hook file
    hook_file.write_text(HOOK_CODE)
    hook_file.chmod(0o755)
    print(f"✓ Installed {hook_file}")

    # Update settings.json
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except:
            pass

    # Merge hooks (don't overwrite other hooks)
    existing_hooks = settings.get("hooks", {})

    # Add CFA hooks to PreToolUse
    pre_tool_use = existing_hooks.get("PreToolUse", [])

    # Remove any existing CFA hooks first
    pre_tool_use = [h for h in pre_tool_use if "cfa_enforce" not in str(h)]

    # Add new CFA hooks
    pre_tool_use.extend(HOOKS_CONFIG["PreToolUse"])

    existing_hooks["PreToolUse"] = pre_tool_use
    settings["hooks"] = existing_hooks

    settings_file.write_text(json.dumps(settings, indent=2))
    print(f"✓ Updated {settings_file}")

    print()
    print("Installation complete!")
    print()
    print("The hook will enforce:")
    print("  - cfa.onboard() must be called before Edit/Write")
    print("  - Only applies to projects with .claude/ directory")
    print()
    print("Restart Claude Code for changes to take effect.")


def remove():
    """Remove CFA v4 hooks."""
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_file = claude_dir / "settings.json"
    hook_file = hooks_dir / "cfa_enforce.py"

    print("CFA v4 Uninstaller")
    print("=" * 40)

    # Remove hook file
    if hook_file.exists():
        hook_file.unlink()
        print(f"✓ Removed {hook_file}")

    # Remove from settings.json
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
            hooks = settings.get("hooks", {})
            pre_tool_use = hooks.get("PreToolUse", [])

            # Remove CFA hooks
            pre_tool_use = [h for h in pre_tool_use if "cfa_enforce" not in str(h)]

            if pre_tool_use:
                hooks["PreToolUse"] = pre_tool_use
            else:
                hooks.pop("PreToolUse", None)

            if hooks:
                settings["hooks"] = hooks
            else:
                settings.pop("hooks", None)

            settings_file.write_text(json.dumps(settings, indent=2))
            print(f"✓ Updated {settings_file}")
        except Exception as e:
            print(f"⚠ Could not update settings: {e}")

    # Remove state file
    state_file = claude_dir / "cfa_session_state.json"
    if state_file.exists():
        state_file.unlink()
        print(f"✓ Removed {state_file}")

    print()
    print("Uninstallation complete!")


def main():
    """CLI entry point."""
    if "--remove" in sys.argv or "--uninstall" in sys.argv:
        remove()
    elif "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
    else:
        install()


if __name__ == "__main__":
    main()
