"""Módulo de prompts e instruction providers do Professor Virtual."""

from .prompts import (
    GLOBAL_INSTRUCTION,
    INSTRUCTION,
    INSTRUCTION_PROVIDERS,
    professor_instruction_provider,
    erro_instruction_provider,
    boas_vindas_provider
)

__all__ = [
    "GLOBAL_INSTRUCTION",
    "INSTRUCTION", 
    "INSTRUCTION_PROVIDERS",
    "professor_instruction_provider",
    "erro_instruction_provider",
    "boas_vindas_provider"
]