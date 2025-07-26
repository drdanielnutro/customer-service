# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Callback functions for Professor Virtual Educational Agent."""

import logging
import time

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from typing import Any, Dict, Optional, Tuple
from google.adk.tools import BaseTool
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.state import State
from google.adk.tools.tool_context import ToolContext
from jsonschema import ValidationError
from professor_virtual.entities.student import Student

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RATE_LIMIT_SECS = 60
RPM_QUOTA = 10


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> None:
    """Callback function that implements a query rate limit.

    Args:
      callback_context: A CallbackContext obj representing the active callback
        context.
      llm_request: A LlmRequest obj representing the active LLM request.
    """
    for content in llm_request.contents:
        for part in content.parts:
            if part.text=="":
                part.text=" "

    
    

    now = time.time()
    if "timer_start" not in callback_context.state:

        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
        logger.debug(
            "rate_limit_callback [timestamp: %i, "
            "req_count: 1, elapsed_secs: 0]",
            now,
        )
        return

    request_count = callback_context.state["request_count"] + 1
    elapsed_secs = now - callback_context.state["timer_start"]
    logger.debug(
        "rate_limit_callback [timestamp: %i, request_count: %i,"
        " elapsed_secs: %i]",
        now,
        request_count,
        elapsed_secs,
    )

    if request_count > RPM_QUOTA:
        delay = RATE_LIMIT_SECS - elapsed_secs + 1
        if delay > 0:
            logger.debug("Sleeping for %i seconds", delay)
            time.sleep(delay)
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
    else:
        callback_context.state["request_count"] = request_count

    return

def validate_student_id(student_id: str, session_state: State) -> Tuple[bool, str]:
    """Validate the student ID against the student profile in the session state."""
    if "student_profile" not in session_state:
        return False, "No student profile selected. Please select a profile."

    try:
        s = Student.model_validate_json(session_state["student_profile"])
        if student_id == s.student_id:
            return True, None
        return (
            False,
            "You cannot use the tool with student_id "
            + student_id
            + ", only for "
            + s.student_id
            + ".",
        )
    except ValidationError:
        return False, "Student profile couldn't be parsed. Please reload the student data. "

def lowercase_value(value):
    """Make dictionary lowercase"""
    if isinstance(value, dict):
        return (dict(k, lowercase_value(v)) for k, v in value.items())
    elif isinstance(value, str):
        return value.lower()
    elif isinstance(value, (list, set, tuple)):
        tp = type(value)
        return tp(lowercase_value(i) for i in value)
    else:
        return value


# Callback Methods
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

def after_tool(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:

  # The after_tool callback is a no-op in the educational context.
  return None

# checking that the customer profile is loaded as state.
def before_agent(callback_context: InvocationContext):
    # In a production agent, this is set as part of the
    # session creation for the agent. 
    if "student_profile" not in callback_context.state:
        student_id = callback_context.state.get("student_id", "default_student")
        callback_context.state["student_profile"] = Student.get_student(
            student_id
        ).to_json()

    # logger.info(callback_context.state["student_profile"])
