from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # NVIDIA NIM — LLM for step generation (OpenAI-compatible)
    nim_api_key: str = ""
    nim_model: str = "meta/llama-3.3-70b-instruct"
    replicate_api_token: str = ""
    flux_num_inference_steps: int = 28
    flux_guidance: float = 7.5
    # Affine warp FLUX→original often hurts when FLUX reshapes the face (double eyes, smears).
    # Set FLUX_FACE_ALIGN=true only if you see offset without warp.
    flux_face_align: bool = False
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174,"
        "http://localhost:5175,http://127.0.0.1:5175"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
