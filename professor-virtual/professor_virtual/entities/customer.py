"""Student entity module."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class Student(BaseModel):
    """Represents a student."""

    student_id: str
    name: str
    grade: str
    model_config = ConfigDict(from_attributes=True)

    def to_json(self) -> str:
        """Return the Student as a JSON string."""
        return self.model_dump_json(indent=4)

    @staticmethod
    def get_student(current_student_id: str) -> Optional["Student"]:
        """Retrieve a student based on an ID."""
        return Student(student_id=current_student_id, name="João", grade="5º ano")
