"""Agent module for the Professor Virtual agent."""

import logging
import warnings
from google.adk import Agent
from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .instruction_providers import professor_instruction_provider
from .shared_libraries.callbacks import (
    rate_limit_callback,
    before_agent,
    before_tool,
    after_tool,
)
from .tools import (
    transcrever_audio,
    analisar_necessidade_visual,
    analisar_imagem_educacional,
    gerar_audio_tts,
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()
logger = logging.getLogger(__name__)

root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction="",
    instruction=professor_instruction_provider,
    name=configs.agent_settings.name,
    tools=[
        transcrever_audio,
        analisar_necessidade_visual,
        analisar_imagem_educacional,
        gerar_audio_tts,
    ],
    generate_content_config=configs.generate_content_config,
    before_tool_callback=before_tool,
    after_tool_callback=after_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
