"""
MCP Tool: kg.omitted

List what was omitted from a previous retrieval and why.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path


async def kg_omitted(
    omitted_chunks: List[Dict[str, Any]],
    filter_reason: Optional[str] = None,
    filter_type: Optional[str] = None,
    sort_by: str = "relevance"
) -> Dict[str, Any]:
    """
    Analyze and filter omitted chunks from a previous kg.retrieve.

    Use this to understand what context was NOT loaded and plan
    which chunks to load next with kg.get or kg.expand.

    Args:
        omitted_chunks: The omitted_chunks list from kg.retrieve result
        filter_reason: Filter by omission reason (token_budget, low_relevance, etc.)
        filter_type: Filter by chunk type (function, test, config, etc.)
        sort_by: Sort order: "relevance" (default), "tokens", "type"

    Returns:
        Dictionary with:
            - success: Boolean
            - filtered_count: Number after filtering
            - total_count: Original count
            - summary: Summary of omissions
            - by_reason: Grouped by reason
            - by_type: Grouped by type
            - high_value: Top chunks worth loading
            - chunks: Filtered and sorted chunk list

    Examples:
        # Get previous retrieval result
        retrieve_result = await kg_retrieve(...)

        # Analyze all omissions
        result = await kg_omitted(
            omitted_chunks=retrieve_result["omitted_chunks"]
        )

        # Focus on high-relevance omissions
        result = await kg_omitted(
            omitted_chunks=retrieve_result["omitted_chunks"],
            filter_reason="token_budget",
            sort_by="relevance"
        )

        # See omitted tests specifically
        result = await kg_omitted(
            omitted_chunks=retrieve_result["omitted_chunks"],
            filter_type="test"
        )

    CRITICAL - Omission Transparency:
        This tool helps you understand what you DON'T know.
        Always check omissions after kg.retrieve to ensure
        you haven't missed critical context.

    Best Practice:
        1. After kg.retrieve, review this output
        2. Identify high-value omissions (high relevance but token_budget reason)
        3. Use kg.get to load those specific chunks
        4. Or adjust token_budget in next kg.retrieve
    """
    try:
        if not omitted_chunks:
            return {
                "success": True,
                "filtered_count": 0,
                "total_count": 0,
                "summary": "No omissions - all relevant chunks were loaded.",
                "chunks": []
            }

        # Filter
        filtered = omitted_chunks.copy()

        if filter_reason:
            filtered = [c for c in filtered if c.get("reason") == filter_reason]

        if filter_type:
            filtered = [c for c in filtered if c.get("chunk_type") == filter_type]

        # Sort
        if sort_by == "relevance":
            filtered.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
        elif sort_by == "tokens":
            filtered.sort(key=lambda c: c.get("token_count", 0), reverse=True)
        elif sort_by == "type":
            filtered.sort(key=lambda c: c.get("chunk_type", ""))

        # Group by reason
        by_reason: Dict[str, List] = {}
        for chunk in omitted_chunks:
            reason = chunk.get("reason", "unknown")
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(chunk)

        # Group by type
        by_type: Dict[str, List] = {}
        for chunk in omitted_chunks:
            chunk_type = chunk.get("chunk_type", "unknown")
            if chunk_type not in by_type:
                by_type[chunk_type] = []
            by_type[chunk_type].append(chunk)

        # Identify high-value omissions
        high_value = [
            c for c in omitted_chunks
            if c.get("reason") == "token_budget" and c.get("relevance_score", 0) > 0.5
        ]
        high_value.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
        high_value = high_value[:10]

        # Calculate totals
        total_omitted_tokens = sum(c.get("token_count", 0) for c in omitted_chunks)

        # Build summary
        reason_counts = {r: len(chunks) for r, chunks in by_reason.items()}
        type_counts = {t: len(chunks) for t, chunks in by_type.items()}

        summary = (
            f"{len(omitted_chunks)} chunks omitted ({total_omitted_tokens:,} tokens). "
            f"Primary reason: {max(reason_counts, key=reason_counts.get) if reason_counts else 'none'}. "
            f"{len(high_value)} high-value chunks available for expansion."
        )

        return {
            "success": True,
            "filtered_count": len(filtered),
            "total_count": len(omitted_chunks),
            "total_omitted_tokens": total_omitted_tokens,
            "summary": summary,
            "by_reason": {r: len(chunks) for r, chunks in by_reason.items()},
            "by_type": {t: len(chunks) for t, chunks in by_type.items()},
            "high_value": high_value,
            "chunks": filtered,
            "recommendation": (
                f"Load high-value chunks using: kg.get(chunk_ids={[c['id'] for c in high_value[:5]]})"
                if high_value else "No high-value omissions to recommend."
            )
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze omissions: {str(e)}"
        }
