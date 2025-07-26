import logging
from google.adk.agents.invocation_context import InvocationContext
from professor_virtual.entities.student import Student

logger = logging.getLogger(__name__)


def before_agent(callback_context: InvocationContext):
    # In a production agent, this is set as part of the
    # session creation for the agent. 
    if "student_profile" not in callback_context.state:
        student_id = callback_context.state.get("student_id", "default_student")
        callback_context.state["student_profile"] = Student.get_student(
            student_id
        ).to_json()

    # logger.info(callback_context.state["student_profile"])
