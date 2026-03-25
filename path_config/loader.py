"""配置加载器"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .loaders import DEFAULT_LOADERS, Loader


class ConfigLoader:
    """多路径配置文件加载器

    支持格式：JSON, YAML, TOML

    用法：
        loader = ConfigLoader(paths=[
            Path("config.yaml"),
            ("xdg", "myapp/config.yaml"),
            ("cwd", ".myapp.yaml"),
        ])
        config = loader.load()
    """

    def __init__(
        self,
        env_var: str | None = None,
        paths: list[Path | tuple[str, str]] | None = None,
        loaders: dict[str, Loader] | None = None,
    ) -> None:
        """初始化配置加载器

        Args:
            env_var: 环境变量名，指向配置文件路径（最高优先级）
            paths: 搜索路径列表，支持 Path 对象或元组 ("xdg"|"cwd", filename)
            loaders: 文件扩展名到加载器的映射
        """
        self.env_var = env_var
        self.paths: list[Path] = []
        self._loaders = loaders or DEFAULT_LOADERS.copy()

        if paths:
            for p in paths:
                if isinstance(p, Path):
                    self.paths.append(p)
                else:
                    scope, filename = p
                    if scope == "xdg":
                        self.paths.append(self._xdg_config_path(filename))
                    elif scope == "cwd":
                        self.paths.append(Path.cwd() / filename)

    @staticmethod
    def _xdg_config_path(filename: str) -> Path:
        """获取 XDG 配置目录下的文件路径"""
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", "~"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))
        return base / filename

    def _get_loader(self, path: Path) -> Loader | None:
        """根据文件扩展名获取加载器"""
        suffix = path.suffix.lower()
        return self._loaders.get(suffix)

    def load(self, default: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """加载配置

        搜索顺序：
        1. 环境变量指定的路径（如果设置了 env_var）
        2. paths 列表中的路径（按添加顺序）

        Args:
            default: 未找到配置时的默认值

        Returns:
            加载的配置字典，未找到返回 default
        """
        # 优先级 1：环境变量
        if self.env_var and (env_path := os.environ.get(self.env_var)):
            p = Path(env_path)
            if p.exists():
                return self._load_file(p)

        # 优先级 2：路径列表
        for p in self.paths:
            if p.exists():
                return self._load_file(p)

        return default

    def _load_file(self, path: Path) -> dict[str, Any]:
        """从文件加载配置"""
        loader = self._get_loader(path)
        if loader is None:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        return loader.load(path.read_text(encoding="utf-8"))
