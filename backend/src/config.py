from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./venturesignal.db"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    yc_api_base: str = "https://yc-oss.github.io/api"
    score_batch_size: int = 20
    rate_limit_rps: int = 2
    model_name: str = "claude-sonnet-4-5-20250929"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
