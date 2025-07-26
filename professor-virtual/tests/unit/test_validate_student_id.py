from professor_virtual.entities.student import Student
from professor_virtual.shared_libraries.callbacks.validate_student_id.validate_student_id_callback import validate_student_id


def test_validate_student_id_success():
    state = {"student_profile": Student.get_student("55").to_json()}
    valid, err = validate_student_id("55", state)
    assert valid
    assert err is None


def test_validate_student_id_failure():
    state = {"student_profile": Student.get_student("55").to_json()}
    valid, err = validate_student_id("99", state)
    assert not valid
    assert "99" in err
