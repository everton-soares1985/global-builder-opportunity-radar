"""YAML and environment configuration loader.

Configuration:
- GBR_CONFIG_DIR overrides the default config directory.
- GBR_DATABASE_PATH overrides the default SQLite database.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from global_builder_radar.models import SourceConfig


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    configured = os.getenv("GBR_CONFIG_DIR")
    return Path(configured).resolve() if configured else project_root() / "config"


def database_path() -> Path:
    configured = os.getenv("GBR_DATABASE_PATH")
    return Path(configured).resolve() if configured else project_root() / "data" / "radar.sqlite3"


class RadarConfig(BaseModel):
    sources: list[SourceConfig]


class ProfileRules(BaseModel):
    include_keywords: dict[str, float] = Field(default_factory=dict)
    exclude_keywords: dict[str, float] = Field(default_factory=dict)
    category_weights: dict[str, float] = Field(default_factory=dict)
    source_weights: dict[str, float] = Field(default_factory=dict)
    bonuses: dict[str, float] = Field(default_factory=dict)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


def load_radar_config() -> RadarConfig:
    return RadarConfig.model_validate(_read_yaml(config_dir() / "sources.yaml"))


def load_profile_rules() -> ProfileRules:
    return ProfileRules.model_validate(_read_yaml(config_dir() / "profile_rules.yaml"))
