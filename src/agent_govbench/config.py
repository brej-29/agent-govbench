"""Runtime configuration, read from .env and the environment. Nothing is hardcoded here."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]

# Bucket prefixes this project may write to. Project B owns contract/, raw/, data/, tuning/, replay_results/.
OWN_PREFIXES = ("gold/", "scenarios/", "replay/", "traces/", "report/")  # contract v0 layout; raw/ is B-internal per B README


def _req(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required setting {name} (set it in .env)")
    return value


@dataclass(frozen=True)
class Config:
    project: str
    region: str
    model_location: str
    bucket: str
    agent_model: str
    judge_model: str
    guard_model: str

    def gcs_uri(self, prefix: str, path: str = "") -> str:
        if not any(prefix.startswith(p) for p in OWN_PREFIXES):
            raise ValueError(f"Refusing to write outside own prefixes: {prefix}")
        return f"gs://{self.bucket}/{prefix}{path}"


@lru_cache(maxsize=1)
def get_config() -> Config:
    load_dotenv(REPO_ROOT / ".env")
    return Config(
        project=_req("GOOGLE_CLOUD_PROJECT"),
        region=_req("GOOGLE_CLOUD_LOCATION"),
        model_location=_req("GOVBENCH_MODEL_LOCATION"),
        bucket=_req("GOVBENCH_BUCKET"),
        agent_model=_req("GOVBENCH_AGENT_MODEL"),
        judge_model=_req("GOVBENCH_JUDGE_MODEL"),
        guard_model=_req("GOVBENCH_GUARD_MODEL"),
    )
