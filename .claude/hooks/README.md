# CFA Enforcement Hooks

Automatic protocol enforcement for Context-First Architecture v3.

## What These Hooks Do

| Hook | Event | Action |
|------|-------|--------|
| **SessionStart** | New session begins | Detect CFA project, remind onboarding protocol |
| **PreToolUse (Edit/Write)** | Before file modifications | Warn if `kg.retrieve` not called yet |
| **PostToolUse (Edit)** | After file modifications | Remind `contract.check_breaking` if functions changed |
| **Stop** | Session ending | Remind pending actions (kg.build, memory.set) |

## Enforcement Level: Medium

- **Warns** but doesn't block edits without context (first time)
- **Tracks** modified files and functions automatically
- **Reminds** about pending documentation at session end

## Files

```
~/.claude/
├── hooks/
│   └── cfa_validator.py    # Main validator script
├── settings.json            # Hook configuration
└── cfa_session_state.json   # Session state (auto-generated)
```

## Installation

Already installed globally. To reinstall:

```bash
# From CFA project root
cp .claude/hooks/cfa_validator.py ~/.claude/hooks/
```

Then add hooks to `~/.claude/settings.json` (see `cfa_hooks_config.json` for template).

## Session State

The validator tracks:
- `onboarding_done` - Was `workflow.onboard` called?
- `kg_retrieve_done` - Was context loaded before editing?
- `files_modified` - Which files were changed?
- `functions_modified` - Which functions might have breaking changes?
- `kg_build_pending` - Does Knowledge Graph need rebuilding?

State is stored in `~/.claude/cfa_session_state.json` and resets each session.

## Customization

### Disable Hooks Temporarily

Edit `~/.claude/settings.json` and remove the `hooks` section.

### Stricter Enforcement

Modify `cfa_validator.py`:

```python
# In handle_pre_edit(), change from warning to blocking:
if not state.get("kg_retrieve_done", False):
    print("Must call kg.retrieve before editing", file=sys.stderr)
    sys.exit(2)  # Exit 2 = block action
```

### Add More Checks

Add new matchers in settings.json:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "python3 ~/.claude/hooks/cfa_validator.py"
    }
  ]
}
```

## Protocol Enforced

```
Session Start
    │
    ▼
┌──────────────────────────────────┐
│  1. workflow.onboard()           │ ◄── SessionStart reminds
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  2. kg.retrieve(task="...")      │ ◄── PreToolUse warns if missing
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  3. Make changes (Edit/Write)    │ ◄── PostToolUse tracks changes
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  4. contract.check_breaking()    │ ◄── PostToolUse reminds
└──────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────┐
│  5. kg.build() + memory.set()    │ ◄── Stop reminds
└──────────────────────────────────┘
```

## Troubleshooting

### Hooks not triggering

1. Check `/hooks` command in Claude Code
2. Verify `~/.claude/settings.json` has hooks section
3. Test manually: `echo '{"hook_event_name":"SessionStart"}' | python3 ~/.claude/hooks/cfa_validator.py`

### Python not found

Ensure `python3` is in PATH, or update command to full path:
```json
"command": "/usr/bin/python3 ~/.claude/hooks/cfa_validator.py"
```
