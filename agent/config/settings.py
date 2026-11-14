"""
CloudPulse Agent Configuration
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

AGENT_VERSION = "1.0.0"
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "agent_config.json"


@dataclass
class AgentConfig:
    server_url: str = "http://localhost:8000"
    server_id: str = ""
    agent_token: str = ""
    collection_interval: int = 5  # seconds
    heartbeat_interval: int = 15  # seconds
    max_queue_size: int = 120    # buffer up to 10 minutes of metrics at 5s interval
    timeout_seconds: int = 5
    max_retries: int = 4
    agent_version: str = AGENT_VERSION

    @classmethod
    def load(cls) -> "AgentConfig":
        config = cls()
        # 1. Load from file if exists
        if CONFIG_FILE_PATH.exists():
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if hasattr(config, k):
                            setattr(config, k, v)
            except Exception as e:
                print(f"[Warning] Failed to load {CONFIG_FILE_PATH}: {e}")

        # 2. Environment variables override
        config.server_url = os.getenv("CLOUDPULSE_SERVER_URL", config.server_url)
        config.server_id = os.getenv("CLOUDPULSE_SERVER_ID", config.server_id)
        config.agent_token = os.getenv("CLOUDPULSE_AGENT_TOKEN", config.agent_token)
        if os.getenv("CLOUDPULSE_INTERVAL"):
            try:
                config.collection_interval = int(os.getenv("CLOUDPULSE_INTERVAL"))
            except ValueError:
                pass
        return config

    def save(self):
        try:
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
            print(f"[Info] Agent configuration saved to {CONFIG_FILE_PATH}")
        except Exception as e:
            print(f"[Error] Failed to save {CONFIG_FILE_PATH}: {e}")
