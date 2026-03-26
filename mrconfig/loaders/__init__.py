"""配置加载器"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore[assignment]

import yaml


class Loader(ABC):
    """配置加载器基类"""

    @abstractmethod
    def load(self, text: str) -> dict[str, Any]:
        """从文本加载配置"""
        ...


class JsonLoader(Loader):
    """JSON 加载器"""

    def load(self, text: str) -> dict[str, Any]:
        return json.loads(text)  # type: ignore[no-any-return]


class YamlLoader(Loader):
    """YAML 加载器"""

    def load(self, text: str) -> dict[str, Any]:
        return yaml.safe_load(text) or {}


class TomlLoader(Loader):
    """TOML 加载器"""

    def load(self, text: str) -> dict[str, Any]:
        if tomllib is None:
            raise ImportError(
                "tomllib is required for TOML support. Use Python 3.11+ or install tomllib."
            )
        return tomllib.loads(text)


# 默认加载器映射
DEFAULT_LOADERS: dict[str, Loader] = {
    ".json": JsonLoader(),
    ".yaml": YamlLoader(),
    ".yml": YamlLoader(),
    ".toml": TomlLoader(),
}
