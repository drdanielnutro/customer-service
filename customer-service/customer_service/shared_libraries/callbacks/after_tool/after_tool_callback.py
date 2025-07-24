import logging
from typing import Any, Dict, Optional
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def after_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:

  # After approvals, we perform operations deterministically in the callback
  # to apply the discount in the cart.
  if tool.name == "sync_ask_for_approval":
    if tool_response['status'] == "approved":
        logger.debug("Applying discount to the cart")
        # Actually make changes to the cart

  if tool.name == "approve_discount":
    if tool_response['status'] == "ok":
        logger.debug("Applying discount to the cart")
        # Actually make changes to the cart

