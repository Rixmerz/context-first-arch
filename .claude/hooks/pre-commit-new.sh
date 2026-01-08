#!/bin/bash
# CFA Pre-commit Hook - Mandatory Documentation Before Commit
#
# After code changes, you MUST use these tools BEFORE committing:
# - kg.build() → If you modified code files
# - contract.check_breaking() → If you modified function signatures
# - memory.set() → If you discovered important patterns/gotchas
#
# This hook BLOCKS commits that skip these tools.
# Bypass: git commit --no-verify

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Check if CFA project
if [ ! -f ".claude/settings.json" ] || ! grep -q "cfa_version" ".claude/settings.json"; then
    exit 0
fi

# Get staged files
STAGED=$(git diff --cached --name-only --diff-filter=ACMR)

# Check for code changes (exclude docs, tests, configs)
CODE_CHANGED=$(echo "$STAGED" | grep -E '\.(py|ts|tsx|js|jsx|java|go|rs)$' | grep -v test | grep -v __pycache__ || true)

if [ -z "$CODE_CHANGED" ]; then
    # No code changes, allow commit
    echo -e "${GREEN}✓ No code changes - commit allowed${NC}"
    exit 0
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}CFA Pre-commit Hook - MANDATORY DOCUMENTATION${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "You modified code files. You MUST run these BEFORE committing:"
echo ""

# Check what was modified to determine required tools
NEEDS_KG=0
NEEDS_CONTRACT=0
NEEDS_MEMORY=0

# 1. Code changes → need kg.build
if [ -n "$CODE_CHANGED" ]; then
    NEEDS_KG=1
    echo -e "${RED}❌ REQUIRED: kg.build(incremental=true)${NC}"
    echo "   You modified code - Knowledge Graph must be updated"
fi

# 2. Check for function modifications → need contract.check_breaking
for file in $CODE_CHANGED; do
    if git diff --cached "$file" | grep -E "^\+.*(def |async def |function )" > /dev/null; then
        NEEDS_CONTRACT=1
        break
    fi
done

if [ $NEEDS_CONTRACT -eq 1 ]; then
    echo -e "${RED}❌ REQUIRED: contract.check_breaking(symbol=\"...\")${NC}"
    echo "   You modified function signatures - breaking changes must be checked"
fi

# 3. Suggest memory if significant changes
LINES_CHANGED=$(git diff --cached | wc -l)
if [ $LINES_CHANGED -gt 50 ]; then
    NEEDS_MEMORY=1
    echo -e "${YELLOW}⚠️  RECOMMENDED: memory.set(key=\"...\", tags=[\"...\"])${NC}"
    echo "   Significant changes - save any learnings discovered"
fi

echo ""
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}COMMIT BLOCKED until tools are executed${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Run these commands in Claude, then retry:"
echo "  1. kg.build(project_path=\".\", incremental=true)"
if [ $NEEDS_CONTRACT -eq 1 ]; then
    echo "  2. contract.check_breaking(project_path=\".\", symbol=\"modified_function\")"
fi
if [ $NEEDS_MEMORY -eq 1 ]; then
    echo "  3. memory.set(project_path=\".\", key=\"...\", value=\"...\", tags=[...])"
fi
echo ""
echo "Then: git commit"
echo ""
echo "Bypass: git commit --no-verify"
echo ""

exit 2
