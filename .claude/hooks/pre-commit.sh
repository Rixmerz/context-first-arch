#!/bin/bash
# CFA Pre-commit Hook - Enforce Knowledge Graph updates
#
# This hook ensures the Knowledge Graph is built before committing code changes.
# It prevents stale KG issues and maintains context accuracy.
#
# Bypass: git commit --no-verify

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if this is a CFA project
if [ ! -f ".claude/settings.json" ] || ! grep -q "cfa_version" ".claude/settings.json"; then
    exit 0  # Not a CFA project, skip
fi

# Check if .claude exists
if [ ! -d ".claude" ]; then
    exit 0
fi

# Get the list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR)

# Check if any actual code files were changed (exclude docs, tests, etc.)
CODE_FILES=$(echo "$STAGED_FILES" | grep -E '\.(py|ts|tsx|js|jsx|java|go|rs|rb|php)$' || true)

# If only docs/tests changed, skip
if [ -z "$CODE_FILES" ]; then
    exit 0
fi

# Check if KG was recently built
KG_DB=".claude/knowledge_graph.db"

if [ ! -f "$KG_DB" ]; then
    echo -e "${RED}⚠️  CFA ERROR: Knowledge Graph not found${NC}"
    echo -e "${YELLOW}Run: kg.build(project_path=\".\")${NC}"
    exit 1
fi

# Check if KG is stale (older than 1 day)
if [ -f "$KG_DB" ]; then
    KG_AGE=$(($(date +%s) - $(stat -f%m "$KG_DB" 2>/dev/null || stat -c%Y "$KG_DB" 2>/dev/null || echo 0)))
    KG_AGE_HOURS=$((KG_AGE / 3600))

    if [ $KG_AGE_HOURS -gt 24 ]; then
        echo -e "${YELLOW}⚠️  WARNING: Knowledge Graph is stale (${KG_AGE_HOURS}h old)${NC}"
        echo -e "${YELLOW}Consider running: kg.build(project_path=\".\", incremental=true)${NC}"
    fi
fi

# Check for decisions/rules related to files being committed
for file in $CODE_FILES; do
    # Check if file has contracts
    if [ -f "contracts/${file%.py}.contract.md" ] || [ -f "contracts/${file%.ts}.contract.md" ]; then
        # File has contract - good
        continue
    fi

    # Check if it's a new feature file
    if git diff --cached --name-only | grep -q "^src/features/"; then
        echo -e "${YELLOW}ℹ️  New feature file: $file${NC}"
        echo -e "${YELLOW}   Consider: contract.create(impl_file=\"$file\")${NC}"
    fi
done

# Success
echo -e "${GREEN}✓ Pre-commit checks passed${NC}"
exit 0
