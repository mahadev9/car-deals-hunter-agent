import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    LLM_MODEL: str = Field(
        ...,
        description="The language model to use for generating responses. Format: provider:model_name (e.g., 'openai:gpt-5.4')",
    )

    @field_validator("LLM_MODEL")
    def validate_llm_model(cls, value: str) -> str:
        provider, model = value.split(":")
        if provider not in ["lmstudio", "openai", "anthropic", "google_genai"]:
            raise ValueError(
                f"Unsupported provider '{provider}'. Supported providers are: lmstudio, openai, anthropic, google_genai."
            )

        if provider == "lmstudio":
            if "LM_STUDIO_API_KEY" not in os.environ:
                raise ValueError(
                    "LM_STUDIO_API_KEY environment variable is required for lmstudio provider."
                )
            if "LM_STUDIO_BASE_URL" not in os.environ:
                raise ValueError(
                    "LM_STUDIO_BASE_URL environment variable is required for lmstudio provider."
                )
        elif provider == "openai":
            if "OPENAI_API_KEY" not in os.environ:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required for openai provider."
                )
        elif provider == "anthropic":
            if "ANTHROPIC_API_KEY" not in os.environ:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable is required for anthropic provider."
                )
        elif provider == "google_genai":
            if "GEMINI_API_KEY" not in os.environ:
                raise ValueError(
                    "GEMINI_API_KEY environment variable is required for google_genai provider."
                )

        return value
