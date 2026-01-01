# CFA v3 - Advanced Features

## 1. Git Hook: Pre-commit Enforcement

**File:** `.git/hooks/pre-commit`

Runs automatically before each commit. Ensures:
- Knowledge Graph exists
- KG is not stale (checks age)
- New feature files have contracts
- Code files are tracked in CFA

### What it checks
```
Code files changed?
  ├─ KG exists?
  ├─ KG younger than 24h?
  ├─ New features have contracts?
  └─ Remind to kg.build if needed
```

### Bypass
```bash
git commit --no-verify
```

---

## 2. Skill: `/cfa-status`

**File:** `.claude/skills/cfa-status.md`

Display comprehensive dashboard of project health.

### Shows
- Knowledge Graph: Status, chunk count, last build, coverage
- Contracts: Total, valid, outdated
- Memory: Learnings count, tags, last update
- Safe Points: Total checkpoints, last one
- Decisions: Architectural records
- Issues: Functions without contracts, stale KG, breaking changes

### Usage
```
/cfa-status
```

### Next steps from output
- KG Stale? → `kg.build(incremental=true)`
- Contracts outdated? → `contract.sync(impl_file="...")`
- No memory? → `memory.set(key="...", value="...")`
- Many safe points? → Clean old ones

---

## 3. Auto-audit Hook

**File:** `.claude/hooks/cfa_audit.py`

Detects architectural violations and quality issues.

### Audit categories

#### Missing Contracts
Files larger than 500 bytes without contracts.
```
Fix: contract.create(impl_file="...")
```

#### Undocumented Changes
Commits without corresponding decisions.
```
Fix: decision.add(title="...", context="...", decision="...", reason="...")
```

#### Breaking Changes
Function signature modifications detected.
```
Fix: contract.check_breaking(symbol="...")
```

#### Memory Health
No learnings recorded.
```
Fix: memory.set(key="gotcha", value="...", tags=["..."])
```

#### KG Staleness
Knowledge Graph older than 24 hours.
```
Fix: kg.build(incremental=true)
```

### Run on-demand
```python
# In Python
from .claude.hooks.cfa_audit import handle_on_demand
report = handle_on_demand(project_path=".")
```

Or in terminal:
```bash
python3 .claude/hooks/cfa_audit.py .
```

---

## Integration with Hooks

These features work together:

```
git commit
  │
  ▼
.git/hooks/pre-commit
  ├─ Checks code files changed
  ├─ Warns if KG stale
  ├─ Reminds about contracts
  │
  └─ (Internally calls cfa_audit for issues)
```

At session start/end:
```
SessionStart → Show /cfa-status
    │
    ▼
Work session
    │
    ▼
Stop → Remind about /cfa-status checks
```

---

## Best Practices

### Before every commit
```bash
/cfa-status
# Review issues
git commit  # pre-commit hook runs automatically
```

### Daily
```bash
/cfa-status  # Check KG age
kg.build(incremental=true)  # If >24h old
```

### After significant changes
```bash
/cfa-status
contract.check_breaking(symbol="...")
memory.set(key="...", tags=["gotcha"])
decision.add(...)
git commit
```

---

## Customization

### Disable pre-commit hook
```bash
rm .git/hooks/pre-commit
```

### Make pre-commit stricter
Edit `.git/hooks/pre-commit` to block commits instead of warn.

### Add custom audit checks
Edit `.claude/hooks/cfa_audit.py` and add functions like `check_*`.

### Integrate with CI/CD
```bash
# In GitHub Actions
- run: python3 .claude/hooks/cfa_audit.py . > audit.json
- uses: actions/upload-artifact@v2
  with:
    name: cfa-audit
    path: audit.json
```

---

## Troubleshooting

### Pre-commit hook not running
```bash
# Make sure it's executable
chmod +x .git/hooks/pre-commit

# Test manually
./.git/hooks/pre-commit
```

### Status shows many outdated contracts
```bash
# Sync all contracts
for file in contracts/*.contract.md; do
  impl="${file%.contract.md}.py"
  contract.sync(impl_file="$impl")
done
```

### Audit detects stale KG
```bash
# Rebuild incrementally
kg.build(incremental=true)

# Or full rebuild
kg.build(incremental=false)
```
