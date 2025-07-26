import logging
from typing import Any, Dict, Optional
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def after_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """Post-tool callback. No e-commerce logic needed."""

    # The agent no longer manages discounts or carts.
    return None

