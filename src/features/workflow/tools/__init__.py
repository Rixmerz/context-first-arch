"""
Workflow Tools - Session Initialization

2 tools (consolidated to 1 in MCP via show_instructions param):
- workflow_onboard: Load project context at session start
- workflow_instructions: Get CFA usage guide (merged into onboard)
"""

from .workflow_onboard import workflow_onboard
from .workflow_instructions import workflow_instructions

__all__ = ["workflow_onboard", "workflow_instructions"]
