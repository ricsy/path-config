"""配置加载器"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .loaders import DEFAULT_LOADERS, Loader


def _to_kebab_case(name: str) -> str:
    """将下划线命名转换为短横线命名"""
    return name.replace("_", "-")


def _to_env_name(name: str) -> str:
    """将名称转换为环境变量命名"""
    return name.upper().replace("-", "_")


class ConfigLoader:
    """多路径配置文件加载器

    支持格式：JSON, YAML, TOML

    用法：
        loader = ConfigLoader(name=".myapp.yaml", xdg="app/config.yaml")
        config = loader.load()
    """

    def __init__(
        self,
        name: str | None = None,
        xdg: str | None = None,
        env: str | None = None,
        loaders: dict[str, Loader] | None = None,
    ) -> None:
        """初始化配置加载器

        Args:
            name: 配置文件名（当前目录，默认）
            xdg: XDG 配置目录下的路径
            env: 环境变量名，指向配置文件路径（最高优先级）
            loaders: 文件扩展名到加载器的映射
        """
        self.env = env
        self.paths: list[Path] = []
        self._loaders = loaders or DEFAULT_LOADERS.copy()

        if name:
            self.paths.append(Path(name).expanduser().resolve())
        if xdg:
            self.paths.append(self._xdg_config_path(xdg).expanduser().resolve())

    @classmethod
    def from_app(
        cls,
        app: str,
        *,
        use_env: bool = True,
        ext: str = ".yaml",
    ) -> ConfigLoader:
        """从应用名称快速创建配置加载器

        自动推断以下配置：
        - name: .{app}.yaml（当前目录）
        - xdg: {app}/config.yaml（XDG 配置目录）
        - env: {APP}_CONFIG（环境变量，use_env=True 时）

        Args:
            app: 应用名称，如 "test_backup"
            use_env: 是否启用环境变量覆盖
            ext: 配置文件扩展名，默认 .yaml

        Returns:
            配置加载器实例

        Example:
            >>> loader = ConfigLoader.from_app("myapp")
            >>> # 等价于:
            >>> # ConfigLoader(
            >>> #     name=".myapp.yaml",
            >>> #     xdg="myapp/config.yaml",
            >>> #     env="MYAPP_CONFIG",
            >>> # )
        """
        kebab_app = _to_kebab_case(app)
        env_name = f"{_to_env_name(app)}_CONFIG"

        return cls(
            name=f".{app}{ext}",
            xdg=f"{kebab_app}/config{ext}",
            env=env_name if use_env else None,
        )

    def get_paths(self) -> list[Path]:
        """获取所有配置文件路径

        按优先级返回所有可能的配置文件路径（已去重）。

        优先级：
        1. 环境变量指定的路径（如果设置了 env）
        2. name 指定的路径（当前目录）
        3. xdg 指定的路径

        Returns:
            所有可能的配置文件路径列表
        """
        paths: list[Path] = []

        # 优先级 1：环境变量
        if self.env and (env_path := os.environ.get(self.env)):
            paths.append(Path(env_path))

        # 优先级 2 & 3：路径列表
        paths.extend(self.paths)

        # 去重，保持顺序
        return list(dict.fromkeys(paths))

    @staticmethod
    def _xdg_config_path(filename: str) -> Path:
        """获取 XDG 配置目录下的文件路径"""
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
        return base / filename

    def _get_loader(self, path: Path) -> Loader | None:
        """根据文件扩展名获取加载器"""
        suffix = path.suffix.lower()
        return self._loaders.get(suffix)

    def load(self, default: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """加载配置

        搜索顺序：
        1. 环境变量指定的路径（如果设置了 env）
        2. name 指定的路径（当前目录）
        3. xdg 指定的路径

        Args:
            default: 未找到配置时的默认值

        Returns:
            加载的配置字典，未找到返回 default
        """
        if (path := self.get_active_path()) is not None:
            return self._load_file(path)
        return default

    def get_active_path(self) -> Path | None:
        """获取实际生效的配置文件路径

        按优先级检查并返回第一个存在的配置文件路径。

        Returns:
            实际生效的配置文件路径，不存在返回 None
        """
        # 优先级 1：环境变量
        if self.env and (env_path := os.environ.get(self.env)):
            p = Path(env_path).expanduser().resolve()
            if p.exists():
                return p

        # 优先级 2：路径列表
        for p in self.paths:
            if p.exists():
                return p

        return None

    def _load_file(self, path: Path) -> dict[str, Any]:
        """从文件加载配置"""
        loader = self._get_loader(path)
        if loader is None:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        return loader.load(path.read_text(encoding="utf-8"))
