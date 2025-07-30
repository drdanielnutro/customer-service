"""Agent module for the Professor Virtual agent.

FRONTEND INTEGRATION OVERVIEW
=============================

This is the main entry point for the Professor Virtual ADK agent.
Frontend applications (Flutter, React, etc.) interact with this agent
through HTTP endpoints provided by the Runner.

Key Integration Points:
----------------------
1. File Uploads: Use artifact_handler.handle_file_upload() for processing
2. Session Management: Each user interaction requires a session_id
3. Tool Invocation: Tools are called automatically based on user needs

Frontend Request Flow:
---------------------
1. Frontend sends request with action and data
2. Runner processes the request and manages sessions
3. Agent executes appropriate tools based on the request
4. Response is sent back to frontend with results

See artifact_handler.py for detailed frontend integration guidelines.
"""

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
# FRONTEND INTEGRATION: The Runner exposes HTTP endpoints for frontend communication
# The artifact_service is CRITICAL for handling file uploads from frontend
# Without it, frontend file uploads will fail
runner = Runner(
    agent=root_agent,
    app_name=configs.app_name,
    session_service=session_service,
    artifact_service=artifact_service  # CRÍTICO: Deve ser configurado
)

# Frontend endpoints exposed by Runner:
# POST /invoke - Main endpoint for agent invocation
# POST /upload - File upload endpoint (uses artifact_handler)
# GET /session/{session_id} - Get session status
# 
# Frontend must include in all requests:
# - session_id: Unique session identifier
# - user_id: User identifier for tracking
# - action: The action to perform (e.g., "upload_file", "process_audio")
