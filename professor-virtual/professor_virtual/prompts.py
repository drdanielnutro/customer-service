"""Global instruction and instruction for the professor virtual agent."""

from .instruction_providers import professor_instruction_provider

GLOBAL_INSTRUCTION = ""

# A constante INSTRUCTION referencia o provider dinâmico
INSTRUCTION = professor_instruction_provider
