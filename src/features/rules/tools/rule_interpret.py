"""
MCP Tool: rule.interpret

AI interprets potential business rules from code.
Returns proposals for human confirmation.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import hashlib
from datetime import datetime

from src.features.knowledge_graph import ChunkStorage
from src.features.knowledge_graph import (
    BusinessRule,
    BusinessRuleStore,
    RuleStatus,
    RuleCategory,
    interpret_rules_from_code,
)


async def rule_interpret(
    project_path: str,
    chunk_id: Optional[str] = None,
    file_path: Optional[str] = None,
    symbol_name: Optional[str] = None,
    auto_propose: bool = True,
    categories: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Interpret potential business rules from code.

    AI reads code and proposes rules that capture implicit business logic.
    These rules are stored as PROPOSED and await human confirmation.

    Args:
        project_path: Path to CFA project
        chunk_id: Chunk ID to interpret rules from
        file_path: Direct file path to analyze
        symbol_name: Specific symbol to focus on
        auto_propose: Automatically save proposed rules (default True)
        categories: Filter to specific categories (validation, authorization, etc.)

    Returns:
        Dictionary with:
            - success: Boolean
            - proposals: List of proposed rules
            - summary: What was found

    Examples:
        # Interpret rules from a chunk
        result = await rule_interpret(
            project_path="/projects/my-app",
            chunk_id="src/auth.py:authenticate"
        )

        # Interpret rules from a file
        result = await rule_interpret(
            project_path="/projects/my-app",
            file_path="src/validators.py",
            categories=["validation"]
        )

    IMPORTANT - Human-in-the-Loop:
        This tool PROPOSES rules. They are NOT confirmed until a human
        reviews them using rule.confirm. This ensures accuracy of
        captured business knowledge.
    """
    try:
        path = Path(project_path)

        # Validate CFA project
        if not (path / ".claude").exists():
            return {
                "success": False,
                "error": "Not a CFA project (missing .claude/)"
            }

        # Get code to analyze
        code_content = None
        source_file = file_path
        source_symbol = symbol_name
        source_chunk_id = chunk_id

        if chunk_id:
            storage = ChunkStorage(path)
            chunk = storage.get_chunk(chunk_id)
            if chunk:
                code_content = chunk.content
                source_file = chunk.file_path
                source_symbol = chunk.symbol_name
            else:
                return {
                    "success": False,
                    "error": f"Chunk not found: {chunk_id}"
                }
        elif file_path:
            full_path = path / file_path
            if full_path.exists():
                code_content = full_path.read_text()
            else:
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
        else:
            return {
                "success": False,
                "error": "Either chunk_id or file_path is required"
            }

        # Interpret rules
        raw_proposals = interpret_rules_from_code(
            code_content=code_content,
            file_path=source_file,
            symbol_name=source_symbol,
            chunk_id=source_chunk_id
        )

        # Filter by categories if specified
        if categories:
            raw_proposals = [
                p for p in raw_proposals
                if p["category"] in categories
            ]

        # Convert to BusinessRule objects
        proposals = []
        rule_store = BusinessRuleStore(path)

        for i, prop in enumerate(raw_proposals):
            # Generate unique ID
            rule_id = hashlib.md5(
                f"{source_file}:{prop['line']}:{prop['description']}".encode()
            ).hexdigest()[:12]

            # Construct rule text from pattern
            rule_text = _generate_rule_text(prop)

            rule = BusinessRule(
                id=rule_id,
                rule_text=rule_text,
                category=RuleCategory(prop["category"]),
                status=RuleStatus.PROPOSED,
                source_chunk_id=source_chunk_id or f"{source_file}:file",
                source_file=source_file,
                source_symbol=prop.get("symbol_name") or source_symbol,
                source_lines=(prop["line"], prop["line"]),
                interpretation_context=prop["context"],
                confidence=prop["confidence"],
                tags=[prop["category"], "proposed"],
            )

            if auto_propose:
                rule_store.save_rule(rule)

            proposals.append({
                "id": rule.id,
                "rule_text": rule.rule_text,
                "category": rule.category.value,
                "confidence": f"{rule.confidence:.0%}",
                "source_line": prop["line"],
                "code_snippet": prop["code_snippet"],
                "status": "proposed" if auto_propose else "draft"
            })

        # Build summary
        by_category = {}
        for p in proposals:
            cat = p["category"]
            by_category[cat] = by_category.get(cat, 0) + 1

        summary = f"Found {len(proposals)} potential business rules"
        if by_category:
            cat_str = ", ".join(f"{k}: {v}" for k, v in by_category.items())
            summary += f" ({cat_str})"

        return {
            "success": True,
            "proposals": proposals,
            "proposal_count": len(proposals),
            "by_category": by_category,
            "source_file": source_file,
            "source_chunk": source_chunk_id,
            "auto_proposed": auto_propose,
            "summary": summary,
            "message": summary,
            "next_step": "Use rule.confirm to review and confirm these rules" if proposals else "No rules found"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to interpret rules: {str(e)}"
        }


def _generate_rule_text(proposal: Dict) -> str:
    """Generate natural language rule text from proposal."""
    category = proposal["category"]
    description = proposal["description"]
    code = proposal["code_snippet"]

    templates = {
        "validation": f"Data must pass {description.lower()}: `{code[:50]}...`",
        "authorization": f"Access requires {description.lower()}: `{code[:50]}...`",
        "business_logic": f"Business logic: {description.lower()} (`{code[:40]}...`)",
        "constraint": f"Constraint: {description.lower()} (`{code[:40]}...`)",
    }

    return templates.get(category, f"{description}: `{code[:50]}...`")
