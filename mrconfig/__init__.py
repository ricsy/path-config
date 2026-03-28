"""多路径配置文件加载器

支持 JSON、YAML、TOML 格式，兼容 Linux、macOS、Windows。
"""

from .__version__ import __version__
from .loader import ConfigLoader, xdg_config_path
from .loaders import JsonLoader, Loader, TomlLoader, YamlLoader
from .utils import (
    get_active_config_path,
    load_config,
    load_file,
)

__all__ = [
    "ConfigLoader",
    "JsonLoader",
    "Loader",
    "TomlLoader",
    "YamlLoader",
    "get_active_config_path",
    "load_config",
    "load_file",
    "xdg_config_path",
    "__version__",
]
