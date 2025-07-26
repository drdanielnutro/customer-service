import logging
from typing import Tuple
from jsonschema import ValidationError
from google.adk.sessions.state import State
from professor_virtual.entities.student import Student

logger = logging.getLogger(__name__)


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

