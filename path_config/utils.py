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
    path: Path | None = None,
    xdg: str | None = None,
    cwd: str | None = None,
    env_var: str | None = None,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """从多个路径加载配置文件

    搜索顺序：
    1. 环境变量指定的路径（如果提供）
    2. path 参数
    3. xdg 参数
    4. cwd 参数

    Args:
        path: 配置文件路径
        xdg: XDG 配置目录下的文件名
        cwd: 当前目录下的文件名
        env_var: 环境变量名，指向配置文件路径
        default: 未找到配置时的默认值

    Returns:
        加载的配置字典，未找到返回 default
    """
    loader = ConfigLoader(
        env_var=env_var,
        path=path,
        xdg=xdg,
        cwd=cwd,
    )
    return loader.load(default=default)
