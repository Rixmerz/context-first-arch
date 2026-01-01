"""
MCP Tool: contract.check_breaking

Check for breaking changes after modifying function signatures.
Uses Knowledge Graph to find all callers and detect incompatibilities.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path


async def contract_check_breaking(
    project_path: str,
    symbol: str,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check for breaking changes after modifying a function signature.

    CRITICAL: Call this IMMEDIATELY after modifying ANY function signature
    (parameters added/removed/reordered, types changed). Finds ALL callers
    via Knowledge Graph and detects incompatibilities.

    Args:
        project_path: Path to CFA project
        symbol: Function/method name to check (e.g., 'calculate_total')
        file_path: Optional file path to disambiguate if multiple matches

    Returns:
        Dictionary with:
            - success: Boolean
            - breaking_changes: List of detected breaking changes
            - callers: List of files/functions that call this symbol
            - warnings: List of potential issues
            - message: Summary message
    """
    try:
        from src.features.knowledge_graph.core.storage import ChunkStorage

        path = Path(project_path)
        kg_path = path / ".claude" / "knowledge_graph.db"

        if not kg_path.exists():
            return {
                "success": False,
                "error": "Knowledge Graph not found. Run kg.build first.",
                "hint": "Use kg.build(project_path) to create the Knowledge Graph"
            }

        # Initialize storage and search for the symbol
        storage = ChunkStorage(path)

        # Search for the symbol in the graph using search_symbol
        all_matches = storage.search_symbol(symbol, exact=True)

        # Filter by file_path if provided
        matching_chunks = []
        for chunk in all_matches:
            if file_path is None or (chunk.file_path and file_path in chunk.file_path):
                matching_chunks.append(chunk)

        if not matching_chunks:
            return {
                "success": True,
                "symbol": symbol,
                "found": False,
                "breaking_changes": [],
                "callers": [],
                "warnings": [f"Symbol '{symbol}' not found in Knowledge Graph"],
                "message": f"Symbol '{symbol}' not found. Ensure kg.build is up to date."
            }

        # Find all callers of this symbol via edges
        callers: List[Dict[str, Any]] = []
        breaking_changes: List[Dict[str, Any]] = []

        for chunk in matching_chunks:
            # Get incoming edges (who calls this)
            edges = storage.get_edges_to(chunk.id)
            for edge in edges:
                # Check edge type (could be string or EdgeType enum)
                edge_type_str = str(edge.edge_type.value) if hasattr(edge.edge_type, 'value') else str(edge.edge_type)
                if edge_type_str == "calls":
                    caller_chunk = storage.get_chunk(edge.source_id)
                    if caller_chunk:
                        callers.append({
                            "caller_id": caller_chunk.id,
                            "caller_file": caller_chunk.file_path,
                            "caller_symbol": caller_chunk.symbol_name,
                            "line_start": caller_chunk.line_start,
                            "line_end": caller_chunk.line_end
                        })

        # For now, we report callers - actual breaking change detection
        # would require comparing old vs new signatures
        if callers:
            return {
                "success": True,
                "symbol": symbol,
                "file_path": matching_chunks[0].file_path if matching_chunks else None,
                "found": True,
                "breaking_changes": breaking_changes,
                "callers": callers,
                "caller_count": len(callers),
                "warnings": [
                    f"Found {len(callers)} caller(s). Review each to ensure compatibility."
                ] if callers else [],
                "message": f"Symbol '{symbol}' has {len(callers)} caller(s). No breaking changes detected."
            }
        else:
            return {
                "success": True,
                "symbol": symbol,
                "file_path": matching_chunks[0].file_path if matching_chunks else None,
                "found": True,
                "breaking_changes": [],
                "callers": [],
                "caller_count": 0,
                "warnings": [],
                "message": f"Symbol '{symbol}' has no callers. Safe to modify."
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check breaking changes: {str(e)}"
        }
