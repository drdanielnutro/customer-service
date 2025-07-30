"""Configuration module for the Professor Virtual agent."""

import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AgentModel(BaseModel):
    """Agent model settings."""

    name: str = Field(default="professor_virtual")
    model: str = Field(default="gemini-2.5-flash")


class Config(BaseSettings):
    """Configuration settings for the Professor Virtual agent."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        env_prefix="GOOGLE_",
        case_sensitive=True,
    )
    agent_settings: AgentModel = Field(default=AgentModel())
    generate_content_config: dict = Field(
        default={
            "temperature": 0.7,
            "max_output_tokens": 1000,
            "response_mime_type": "text/plain",
        }
    )
    app_name: str = "professor_virtual_app"
    CLOUD_PROJECT: str = Field(default="my_project")
    CLOUD_LOCATION: str = Field(default="us-central1")
    GENAI_USE_VERTEXAI: str = Field(default="1")
    API_KEY: str | None = Field(default="")
    
    # Configurações do Artifact Service
    artifact_storage_type: str = Field(default="memory", description="memory ou gcs")
    gcs_bucket_name: str = Field(default="adk-professor-virtual-artifacts")
    
    # Configuração de ambiente
    is_production: bool = Field(default=False)
