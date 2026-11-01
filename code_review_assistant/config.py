"""Local-first configuration for the Code Review Assistant.

The project uses the Gemini Developer API (Google AI Studio) by default.
No Google Cloud project, ADC credentials, Vertex AI, or GCS bucket is
required for local development.
"""

import logging
import os
from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentConfig(BaseSettings):
    """Application settings loaded from the project-root .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google AI Studio API key. Vertex AI is deliberately disabled locally.
    google_api_key: str | None = Field(default=None)
    google_genai_use_vertexai: bool = False

    worker_model: str = "gemini-2.5-flash"
    critic_model: str = "gemini-2.5-pro"

    passing_score_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    style_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    test_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    structure_weight: float = Field(default=0.2, ge=0.0, le=1.0)

    max_grading_attempts: int = Field(default=3, gt=0)
    log_level: str = "INFO"
    debug_mode: bool = False

    @model_validator(mode="after")
    def validate_weights(self):
        total = self.style_weight + self.test_weight + self.structure_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Grading weights must sum to 1.0, but got {total}")
        return self

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        value = value.upper()
        if value not in valid:
            raise ValueError(f"Invalid log_level: {value}")
        return value


config = AgentConfig()

# ADK / google-genai reads these environment variables directly.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
if config.google_api_key:
    os.environ["GOOGLE_API_KEY"] = config.google_api_key

logging.getLogger().setLevel(config.log_level)
logger.info("Local Code Review Assistant configuration loaded")
logger.info("Gemini models: worker=%s, critic=%s", config.worker_model, config.critic_model)
