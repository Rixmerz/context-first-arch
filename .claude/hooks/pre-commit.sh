#!/bin/bash
# CFA Pre-commit - Remind to update Knowledge Graph
# Simple version that actually works

# Get staged files
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null)

# Check for Python/TypeScript code changes
if echo "$STAGED_FILES" | grep -qE '\.(py|ts|tsx|js)$'; then
    echo ""
    echo "⚠️  CFA REMINDER: Code files staged"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "After committing, remember to run:"
    echo "  1. kg.build(project_path=\".\", incremental=true)"
    echo "  2. memory.set(key=\"...\", value=\"...\", tags=[...])"
    echo ""
    echo "These ensure your changes are properly documented."
    echo ""
fi

exit 0
