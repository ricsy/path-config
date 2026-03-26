"""工具函数"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .loaders import DEFAULT_LOADERS
from .loader import ConfigLoader


def load_file(path: str | Path) -> dict[str, Any]:
    """加载指定路径的配置文件

    自动展开路径、避免路径攻击、解析文件类型。

    Args:
        path: 配置文件路径

    Returns:
        加载的配置字典

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
    # 展开用户目录并解析为绝对路径，避免路径攻击
    p = Path(path).expanduser().resolve()

    if not p.exists():
        raise FileNotFoundError(f"配置文件不存在: {p}")

    # 根据扩展名获取加载器
    loader = DEFAULT_LOADERS.get(p.suffix.lower())
    if loader is None:
        raise ValueError(f"不支持的文件格式: {p.suffix}")

    return loader.load(p.read_text(encoding="utf-8"))


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
    app: str | None = None,
    *,
    name: str | None = None,
    xdg: str | None = None,
    env: str | None = None,
    use_env: bool = False,
    default: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """从多个路径加载配置文件

    搜索顺序：
    1. 环境变量指定的路径（如果提供了 env 或 app）
    2. name 指定的路径（当前目录）
    3. xdg 指定的路径

    Args:
        app: 应用名称，如提供则自动推断 name/xdg/env
        name: 配置文件名（当前目录）
        xdg: XDG 配置目录下的路径
        env: 环境变量名
        use_env: 是否启用环境变量覆盖（仅 app 模式有效）
        default: 未找到配置时的默认值

    Returns:
        加载的配置字典，未找到返回 default
    """
    if app:
        loader = ConfigLoader.from_app(app, use_env=use_env)
    else:
        loader = ConfigLoader(name=name, xdg=xdg, env=env)
    return loader.load(default=default)


def get_active_config_path(
    app: str | None = None,
    *,
    name: str | None = None,
    xdg: str | None = None,
    env: str | None = None,
    use_env: bool = False,
) -> Path | None:
    """获取实际生效的配置文件路径

    按优先级检查并返回第一个存在的配置文件路径。

    搜索顺序：
    1. 环境变量指定的路径（如果提供了 env 或 app）
    2. name 指定的路径（当前目录）
    3. xdg 指定的路径

    Args:
        app: 应用名称，如提供则自动推断 name/xdg/env
        name: 配置文件名（当前目录）
        xdg: XDG 配置目录下的路径
        env: 环境变量名
        use_env: 是否启用环境变量覆盖（仅 app 模式有效）

    Returns:
        实际生效的配置文件路径，不存在返回 None
    """
    if app:
        loader = ConfigLoader.from_app(app, use_env=use_env)
    else:
        loader = ConfigLoader(name=name, xdg=xdg, env=env)
    return loader.get_active_path()
