from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class ArenaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARENA_", env_file=".env", extra="ignore")
    llm_provider: str = "mock"
    llm_api_key: str = "mock-key"
    llm_base_url: str = ""
    llm_model: str = "mock-v1"
    canary_token: str = "CANARY_SECRET_123"
    max_tokens_per_round: int = 1500
    max_seconds_per_round: float = 15.0
    max_turns_per_round: int = 6
    rate_limit_delay_sec: float = 0.05
    stop_file: str = ".arena_stop"
    data_dir: Path = Path("./data")

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "arena.db"

    @property
    def jsonl_path(self) -> Path:
        return self.data_dir / "arena_events.jsonl"

settings = ArenaSettings()
