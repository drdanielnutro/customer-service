"""Agent module for the Professor Virtual agent."""

import logging
import warnings

from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
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

# Configurar artifact service baseado no ambiente
if configs.is_production and configs.artifact_storage_type == "gcs":
    artifact_service = GcsArtifactService(bucket_name=configs.gcs_bucket_name)
else:
    artifact_service = InMemoryArtifactService()

# Configurar session service
session_service = InMemorySessionService()

# Criar o agente
root_agent = Agent(
    model=configs.agent_settings.model,
    global_instruction="",
    instruction=INSTRUCTION,
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

# Criar o Runner com artifact service
runner = Runner(
    agent=root_agent,
    app_name=configs.app_name,
    session_service=session_service,
    artifact_service=artifact_service,  # CRÍTICO: Deve ser configurado
)
