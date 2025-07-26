import json
from professor_virtual.entities.student import Student


def test_get_student():
    student = Student.get_student("42")
    assert student.student_id == "42"
    assert student.name
    assert student.grade
    # to_json should return a JSON string with the same id
    data = json.loads(student.to_json())
    assert data["student_id"] == "42"
