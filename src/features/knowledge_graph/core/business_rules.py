"""Business Rules - Capture tacit knowledge through human confirmation.

The innovation here is capturing knowledge that ISN'T in the code:
1. AI reads code and INTERPRETS implicit rules
2. AI proposes rules to human for confirmation
3. Human confirms/corrects/rejects
4. Confirmed rules become BUSINESS_RULE chunks

This captures the "why" behind code that documentation often misses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from .models import KnowledgeChunk, ChunkType, ChunkEdge, EdgeType
from .storage import ChunkStorage


class RuleStatus(Enum):
    """Status of a business rule."""
    PROPOSED = "proposed"      # AI proposed, awaiting human review
    CONFIRMED = "confirmed"    # Human confirmed as accurate
    CORRECTED = "corrected"    # Human corrected the rule
    REJECTED = "rejected"      # Human rejected as inaccurate
    DEPRECATED = "deprecated"  # No longer applies


class RuleCategory(Enum):
    """Categories of business rules."""
    VALIDATION = "validation"           # Input validation rules
    AUTHORIZATION = "authorization"     # Access control rules
    BUSINESS_LOGIC = "business_logic"   # Core business logic
    CONSTRAINT = "constraint"           # Data/system constraints
    INVARIANT = "invariant"             # Things that must always be true
    WORKFLOW = "workflow"               # Process/flow rules
    INTEGRATION = "integration"         # External system rules
    SECURITY = "security"               # Security requirements


@dataclass
class BusinessRule:
    """A business rule interpreted from code."""
    id: str
    rule_text: str                      # The rule in natural language
    category: RuleCategory
    status: RuleStatus

    # Source information
    source_chunk_id: str                # Which code chunk this was interpreted from
    source_file: str
    source_symbol: Optional[str]
    source_lines: Optional[tuple]       # (start, end) line numbers

    # Interpretation details
    interpretation_context: str         # What AI saw that suggested this rule
    confidence: float                   # AI's confidence (0.0-1.0)

    # Human feedback
    confirmed_by: Optional[str] = None  # Who confirmed/rejected
    confirmed_at: Optional[datetime] = None
    human_correction: Optional[str] = None  # If corrected, the corrected text
    rejection_reason: Optional[str] = None  # If rejected, why

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def to_chunk(self) -> KnowledgeChunk:
        """Convert to KnowledgeChunk for storage."""
        # Use corrected text if available, otherwise original
        rule_content = self.human_correction or self.rule_text

        content = f"""# Business Rule: {self.id}

**Category**: {self.category.value}
**Status**: {self.status.value}
**Confidence**: {self.confidence:.0%}

## Rule
{rule_content}

## Source
- File: {self.source_file}
- Symbol: {self.source_symbol or 'N/A'}
- Lines: {f"{self.source_lines[0]}-{self.source_lines[1]}" if self.source_lines else 'N/A'}

## Interpretation Context
{self.interpretation_context}
"""

        if self.human_correction:
            content += f"\n## Original (Corrected)\n{self.rule_text}\n"

        if self.rejection_reason:
            content += f"\n## Rejection Reason\n{self.rejection_reason}\n"

        # Compressed version
        compressed = f"[{self.category.value}] {rule_content[:100]}..."

        return KnowledgeChunk(
            id=f"rule:{self.id}",
            chunk_type=ChunkType.BUSINESS_RULE,
            content=content,
            content_compressed=compressed,
            token_count=len(content) // 4,
            token_count_compressed=len(compressed) // 4,
            file_path=self.source_file,
            line_start=self.source_lines[0] if self.source_lines else None,
            line_end=self.source_lines[1] if self.source_lines else None,
            symbol_name=self.source_symbol,
            signature=f"{self.category.value}: {rule_content[:50]}...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            source="human" if self.status in [RuleStatus.CONFIRMED, RuleStatus.CORRECTED] else "ai",
            confidence=1.0 if self.status == RuleStatus.CONFIRMED else self.confidence,
            tags=self.tags + [self.category.value, self.status.value],
            extra={
                "rule_id": self.id,
                "category": self.category.value,
                "status": self.status.value,
                "source_chunk_id": self.source_chunk_id,
                "confirmed_by": self.confirmed_by,
                "original_confidence": self.confidence,
            }
        )

    @classmethod
    def from_chunk(cls, chunk: KnowledgeChunk) -> "BusinessRule":
        """Reconstruct BusinessRule from stored chunk."""
        meta = chunk.extra or {}
        return cls(
            id=meta.get("rule_id", chunk.id.replace("rule:", "")),
            rule_text=chunk.content,  # Will be parsed
            category=RuleCategory(meta.get("category", "business_logic")),
            status=RuleStatus(meta.get("status", "proposed")),
            source_chunk_id=meta.get("source_chunk_id", ""),
            source_file=chunk.file_path or "",
            source_symbol=chunk.symbol_name,
            source_lines=(chunk.line_start, chunk.line_end) if chunk.line_start else None,
            interpretation_context="",
            confidence=meta.get("original_confidence", 0.5),
            confirmed_by=meta.get("confirmed_by"),
            created_at=chunk.created_at,
            updated_at=chunk.updated_at,
            tags=chunk.tags,
        )


class BusinessRuleStore:
    """Manage business rules with SQLite persistence."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.storage = ChunkStorage(project_path)
        self._ensure_table()

    def _ensure_table(self):
        """Create business rules table if not exists."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_rules (
                rule_id TEXT PRIMARY KEY,
                rule_text TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                source_chunk_id TEXT,
                source_file TEXT,
                source_symbol TEXT,
                source_line_start INTEGER,
                source_line_end INTEGER,
                interpretation_context TEXT,
                confidence REAL,
                confirmed_by TEXT,
                confirmed_at TEXT,
                human_correction TEXT,
                rejection_reason TEXT,
                created_at TEXT,
                updated_at TEXT,
                tags TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_rule(self, rule: BusinessRule) -> None:
        """Save a business rule."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO business_rules (
                rule_id, rule_text, category, status,
                source_chunk_id, source_file, source_symbol,
                source_line_start, source_line_end,
                interpretation_context, confidence,
                confirmed_by, confirmed_at, human_correction, rejection_reason,
                created_at, updated_at, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule.id,
            rule.rule_text,
            rule.category.value,
            rule.status.value,
            rule.source_chunk_id,
            rule.source_file,
            rule.source_symbol,
            rule.source_lines[0] if rule.source_lines else None,
            rule.source_lines[1] if rule.source_lines else None,
            rule.interpretation_context,
            rule.confidence,
            rule.confirmed_by,
            rule.confirmed_at.isoformat() if rule.confirmed_at else None,
            rule.human_correction,
            rule.rejection_reason,
            rule.created_at.isoformat(),
            rule.updated_at.isoformat(),
            json.dumps(rule.tags),
        ))

        conn.commit()
        conn.close()

        # Also save as chunk for graph integration
        chunk = rule.to_chunk()
        self.storage.save_chunk(chunk)

        # Create VALIDATES edge
        if rule.status in [RuleStatus.CONFIRMED, RuleStatus.CORRECTED]:
            edge = ChunkEdge(
                source_id=chunk.id,
                target_id=rule.source_chunk_id,
                edge_type=EdgeType.VALIDATES,
                weight=rule.confidence,
                metadata={"category": rule.category.value}
            )
            self.storage.save_edge(edge)

    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """Get a business rule by ID."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return None

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM business_rules WHERE rule_id = ?
        """, (rule_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_rule(row)

    def _row_to_rule(self, row) -> BusinessRule:
        """Convert database row to BusinessRule."""
        return BusinessRule(
            id=row[0],
            rule_text=row[1],
            category=RuleCategory(row[2]),
            status=RuleStatus(row[3]),
            source_chunk_id=row[4],
            source_file=row[5],
            source_symbol=row[6],
            source_lines=(row[7], row[8]) if row[7] else None,
            interpretation_context=row[9],
            confidence=row[10],
            confirmed_by=row[11],
            confirmed_at=datetime.fromisoformat(row[12]) if row[12] else None,
            human_correction=row[13],
            rejection_reason=row[14],
            created_at=datetime.fromisoformat(row[15]) if row[15] else datetime.now(),
            updated_at=datetime.fromisoformat(row[16]) if row[16] else datetime.now(),
            tags=json.loads(row[17]) if row[17] else [],
        )

    def get_rules_for_chunk(self, chunk_id: str) -> List[BusinessRule]:
        """Get all rules that validate a specific chunk."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM business_rules
            WHERE source_chunk_id = ?
            ORDER BY created_at DESC
        """, (chunk_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_rule(row) for row in rows]

    def get_pending_rules(self) -> List[BusinessRule]:
        """Get all rules awaiting human confirmation."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM business_rules
            WHERE status = ?
            ORDER BY confidence DESC, created_at ASC
        """, (RuleStatus.PROPOSED.value,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_rule(row) for row in rows]

    def list_rules(
        self,
        status: Optional[RuleStatus] = None,
        category: Optional[RuleCategory] = None,
        file_path: Optional[str] = None,
        limit: int = 50
    ) -> List[BusinessRule]:
        """List rules with optional filters."""
        import sqlite3
        db_path = self.project_path / ".claude" / "knowledge_graph.db"
        if not db_path.exists():
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        query = "SELECT * FROM business_rules WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if category:
            query += " AND category = ?"
            params.append(category.value)

        if file_path:
            query += " AND source_file LIKE ?"
            params.append(f"%{file_path}%")

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_rule(row) for row in rows]

    def confirm_rule(
        self,
        rule_id: str,
        confirmed_by: str = "human",
        correction: Optional[str] = None
    ) -> Optional[BusinessRule]:
        """Confirm or correct a proposed rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        rule.confirmed_by = confirmed_by
        rule.confirmed_at = datetime.now()
        rule.updated_at = datetime.now()

        if correction:
            rule.status = RuleStatus.CORRECTED
            rule.human_correction = correction
        else:
            rule.status = RuleStatus.CONFIRMED

        self.save_rule(rule)
        return rule

    def reject_rule(
        self,
        rule_id: str,
        reason: str,
        rejected_by: str = "human"
    ) -> Optional[BusinessRule]:
        """Reject a proposed rule."""
        rule = self.get_rule(rule_id)
        if not rule:
            return None

        rule.status = RuleStatus.REJECTED
        rule.rejection_reason = reason
        rule.confirmed_by = rejected_by
        rule.confirmed_at = datetime.now()
        rule.updated_at = datetime.now()

        self.save_rule(rule)
        return rule


def interpret_rules_from_code(
    code_content: str,
    file_path: str,
    symbol_name: Optional[str] = None,
    chunk_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Interpret potential business rules from code.

    This is a heuristic-based interpreter that looks for patterns
    suggesting business rules. In production, this could be enhanced
    with LLM-based interpretation.

    Returns list of proposed rules (not yet BusinessRule objects).
    """
    proposals = []
    lines = code_content.split('\n')

    # Pattern matchers for common rule indicators
    patterns = {
        "validation": [
            (r'if\s+.*(?:len|length)\s*[<>=]', "Length validation"),
            (r'if\s+not\s+\w+:', "Required field check"),
            (r'raise\s+(?:ValueError|ValidationError)', "Validation error"),
            (r'assert\s+', "Assertion/invariant"),
            (r'\.(?:is_valid|validate)\(', "Validation method call"),
        ],
        "authorization": [
            (r'if\s+.*(?:is_admin|has_permission|can_|allowed)', "Permission check"),
            (r'@(?:login_required|permission_required|auth)', "Auth decorator"),
            (r'(?:role|permission)\s*[=!]=', "Role/permission comparison"),
        ],
        "business_logic": [
            (r'if\s+.*(?:status|state)\s*==', "State check"),
            (r'(?:price|cost|amount|total)\s*[*+/-]=?', "Financial calculation"),
            (r'(?:max|min|limit|threshold)', "Limit/threshold"),
        ],
        "constraint": [
            (r'(?:MAX|MIN|LIMIT)_\w+\s*=', "Constant constraint"),
            (r'if\s+.*>\s*\d+', "Numeric constraint"),
            (r'\.(?:startswith|endswith|match)', "Format constraint"),
        ],
    }

    import re
    for i, line in enumerate(lines):
        for category, pattern_list in patterns.items():
            for pattern, description in pattern_list:
                if re.search(pattern, line, re.IGNORECASE):
                    # Extract context (surrounding lines)
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = '\n'.join(lines[start:end])

                    proposals.append({
                        "category": category,
                        "description": description,
                        "line": i + 1,
                        "code_snippet": line.strip(),
                        "context": context,
                        "file_path": file_path,
                        "symbol_name": symbol_name,
                        "chunk_id": chunk_id,
                        "confidence": 0.6,  # Base confidence
                    })
                    break  # One match per line per category

    return proposals
