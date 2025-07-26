from professor_virtual.entities.student import Student
from professor_virtual.shared_libraries.callbacks.before_agent.before_agent_callback import before_agent
from professor_virtual.shared_libraries.callbacks.before_tool.before_tool_callback import before_tool


class DummyInvocation:
    def __init__(self):
        self.state = {"student_id": "77"}


class DummyContext:
    def __init__(self):
        self.state = {"student_profile": Student.get_student("77").to_json()}


class DummyTool:
    pass


def test_before_agent_loads_profile():
    ctx = DummyInvocation()
    before_agent(ctx)
    assert "student_profile" in ctx.state
    profile = Student.model_validate_json(ctx.state["student_profile"])
    assert profile.student_id == "77"


def test_before_tool_validation_ok():
    ctx = DummyContext()
    result = before_tool(DummyTool(), {"student_id": "77"}, ctx)
    assert result is None


def test_before_tool_validation_fail():
    ctx = DummyContext()
    result = before_tool(DummyTool(), {"student_id": "wrong"}, ctx)
    assert isinstance(result, str)
