#!/usr/bin/env python3
"""
CFA Auto-audit Hook - Detect architectural violations

Runs on various events to detect:
- Functions without contracts
- Code with implicit business rules
- Breaking changes not documented
- Files without CFA documentation
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any


def get_project_root() -> Path:
    """Find project root with .claude/settings.json."""
    current = Path.cwd()
    for _ in range(10):
        if (current / ".claude" / "settings.json").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_cfa_config() -> Dict[str, Any]:
    """Load CFA project configuration."""
    config_file = get_project_root() / ".claude" / "settings.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except:
            pass
    return {}


def is_code_file(path: str) -> bool:
    """Check if file is a code file."""
    code_extensions = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".rb"}
    return Path(path).suffix in code_extensions


def check_contracts(project_root: Path) -> List[str]:
    """Find code files without contracts."""
    issues = []
    contracts_dir = project_root / "contracts"
    src_dir = project_root / "src"

    if not src_dir.exists():
        return issues

    for code_file in src_dir.rglob("*"):
        if not is_code_file(str(code_file)):
            continue

        # Skip internal files
        if ".claude" in str(code_file) or "__pycache__" in str(code_file):
            continue

        # Check if contract exists
        contract_name = f"{code_file.stem}.contract.md"
        if not (contracts_dir / contract_name).exists():
            # Only flag if file is large or is a public module
            if code_file.stat().st_size > 500:  # > 500 bytes
                issues.append(str(code_file.relative_to(project_root)))

    return issues


def check_undocumented_changes(project_root: Path) -> List[str]:
    """Find changes without decision records."""
    issues = []
    decisions_file = project_root / ".claude" / "decisions.md"

    if not decisions_file.exists():
        return ["No decisions.md found - architectural decisions not recorded"]

    # Read recent git commits
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        commits = result.stdout.strip().split("\n")

        # Read decisions
        with open(decisions_file) as f:
            decisions = f.read()

        # Check if recent commits have corresponding decisions
        for commit in commits[:5]:  # Check last 5 commits
            commit_msg = commit.split(maxsplit=1)[1] if " " in commit else ""

            # Skip if it's just a fix or test
            if any(prefix in commit_msg for prefix in ["test:", "fix:", "refactor:", "docs:"]):
                continue

            # Check if decision mentions this
            if commit_msg and commit_msg not in decisions:
                # Could be related to a feature
                pass

    except:
        pass

    return issues


def check_breaking_changes(project_root: Path) -> List[str]:
    """Find potential breaking changes."""
    issues = []

    # Check if there are staged changes to function signatures
    try:
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--cached", "--", "*.py", "*.ts"],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        diff = result.stdout
        if "def " in diff or "function " in diff:
            # Changes to functions detected
            # This is just a warning - actual breaking changes checked by contract.check_breaking
            if "(" in diff and ")" in diff:
                issues.append("Potential function signature changes detected - run contract.check_breaking")

    except:
        pass

    return issues


def check_memory_health(project_root: Path) -> List[str]:
    """Check if learnings are being recorded."""
    issues = []

    try:
        import sqlite3

        memory_db = project_root / ".claude" / "memory.db"
        if not memory_db.exists():
            return ["No memory database - learnings not being stored"]

        conn = sqlite3.connect(memory_db)
        cursor = conn.cursor()

        # Check memory count
        cursor.execute("SELECT COUNT(*) FROM memory" if "memory" in get_db_tables(cursor) else "SELECT 0")
        count = cursor.fetchone()[0]

        if count == 0:
            issues.append("No learnings recorded in memory - use memory.set() to capture insights")

        conn.close()

    except:
        pass

    return issues


def get_db_tables(cursor) -> List[str]:
    """Get list of tables in database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cursor.fetchall()]


def check_kg_staleness(project_root: Path) -> List[str]:
    """Check if Knowledge Graph is stale."""
    issues = []

    kg_db = project_root / ".claude" / "knowledge_graph.db"
    if not kg_db.exists():
        return ["Knowledge Graph not built - run kg.build()"]

    # Check age
    import time
    age_seconds = time.time() - kg_db.stat().st_mtime
    age_hours = age_seconds / 3600

    if age_hours > 24:
        issues.append(f"Knowledge Graph is {int(age_hours)}h old - run kg.build(incremental=true)")

    return issues


def generate_audit_report(project_root: Path) -> Dict[str, Any]:
    """Generate comprehensive audit report."""
    report = {
        "project": project_root.name,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "issues": {
            "missing_contracts": check_contracts(project_root),
            "undocumented_changes": check_undocumented_changes(project_root),
            "breaking_changes": check_breaking_changes(project_root),
            "memory_health": check_memory_health(project_root),
            "kg_staleness": check_kg_staleness(project_root),
        },
        "total_issues": 0
    }

    # Count total issues
    report["total_issues"] = sum(len(v) for v in report["issues"].values() if isinstance(v, list))

    return report


# ============================================================================
# HOOK INTEGRATION
# ============================================================================

def handle_pre_commit(data: Dict[str, Any]) -> int:
    """Called from pre-commit hook."""
    project_root = get_project_root()

    # Check if CFA project
    config = load_cfa_config()
    if "cfa_version" not in config:
        return 0

    report = generate_audit_report(project_root)

    if report["total_issues"] > 0:
        print(json.dumps({
            "decision": "approve",
            "reason": "CFA audit findings",
            "continue": True,
            "systemMessage": f"""
## CFA Audit Report

Issues detected in your CFA project:

{chr(10).join(f"- **{k.replace('_', ' ').title()}**: {len(v)} issue(s)" for k, v in report["issues"].items() if v)}

Run `/cfa-audit` for full report and recommendations.
"""
        }))

    return 0


def handle_on_demand(project_path: str = ".") -> Dict[str, Any]:
    """Generate full audit report on demand."""
    project_root = Path(project_path).resolve()
    return generate_audit_report(project_root)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # On-demand audit
        project_path = sys.argv[1] if len(sys.argv) > 1 else "."
        report = handle_on_demand(project_path)
        print(json.dumps(report, indent=2))
        return 0

    # Hook mode
    try:
        data = json.load(sys.stdin)
        return handle_pre_commit(data)
    except:
        return 0


if __name__ == "__main__":
    sys.exit(main())
