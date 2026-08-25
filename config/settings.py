import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    user_agent: str = os.getenv("CRAWLER_USER_AGENT", "PySeekBot/0.1")
    batch_size: int = int(os.getenv("CRAWL_BATCH_SIZE", "5"))
    max_bytes: int = int(os.getenv("CRAWL_MAX_BYTES", str(2 * 1024 * 1024)))


settings = Settings()
