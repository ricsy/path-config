"""工具函数"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .loader import ConfigLoader


def xdg_config_path(filename: str) -> Path:
    r"""获取 XDG 配置目录下的文件路径

    Linux/macOS: ~/.config/{filename}
    Windows: %APPDATA%\{filename}

    Args:
        filename: 配置文件名

    Returns:
        配置文件路径
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", "~"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))
    return base / filename


def load_config(
    paths: list[Path | tuple[str, str]],
    env_var: str | None = None,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """从多个路径加载配置文件

    搜索路径（按顺序优先级）：
    1. 环境变量指定的路径（如果提供）
    2. paths 列表中的路径（按顺序）

    Args:
        paths: 搜索路径列表
        env_var: 环境变量名，指向配置文件路径
        default: 未找到配置时的默认值

    Returns:
        加载的配置字典，未找到返回 default
    """
    loader = ConfigLoader(env_var=env_var, paths=paths)
    return loader.load(default=default)
