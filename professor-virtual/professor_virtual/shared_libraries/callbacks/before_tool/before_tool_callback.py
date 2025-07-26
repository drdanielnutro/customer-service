import logging
from typing import Any, Dict
from google.adk.tools import BaseTool
from google.adk.agents.callback_context import CallbackContext
from ..lowercase_value import lowercase_value
from ..validate_customer_id import validate_student_id

logger = logging.getLogger(__name__)


def before_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: CallbackContext
):

    # i make sure all values that the agent is sending to tools are lowercase
    lowercase_value(args)

    # Several tools require student_id as input. We don't want to rely
    # solely on the model picking the right student id. We validate it.
    # Alternative: tools can fetch the student_id from the state directly.
    if 'student_id' in args:
        valid, err = validate_student_id(args['student_id'], tool_context.state)
        if not valid:
            return err

    # No e-commerce logic should be triggered in the educational context.
    return None

