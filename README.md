# path-config

多路径配置文件加载器，支持 JSON、YAML、TOML 格式。

## 安装

```bash
pip install path-config
```

## 支持格式

| 格式   | 扩展名             | 说明                    |
|------|-----------------|-----------------------|
| JSON | `.json`         | 标准 JSON 格式            |
| YAML | `.yaml`, `.yml` | YAML 格式               |
| TOML | `.toml`         | TOML 格式（Python 3.11+） |

## 使用

```python
from pathlib import Path
from path_config import ConfigLoader

# 单行初始化
loader = ConfigLoader(
    env_var="MYAPP_CONFIG",
    paths=[
        Path("config.yaml"),
        ("xdg", "myapp/config.yaml"),
        ("cwd", ".myapp.yaml"),
    ]
)

config = loader.load(default={"debug": False})
```

### 路径格式

- `Path` 对象：直接使用
- `("xdg", filename)`：XDG 配置目录
- `("cwd", filename)`：当前目录

### XDG 配置路径

| 平台      | 路径                     |
|---------|------------------------|
| Linux   | `~/.config/{filename}` |
| macOS   | `~/.config/{filename}` |
| Windows | `%APPDATA%\{filename}` |

可通过环境变量覆盖：
- Linux/macOS: `XDG_CONFIG_HOME`
- Windows: `APPDATA`

## API

### ConfigLoader

```python
class ConfigLoader:
    def __init__(
        self,
        env_var: str | None = None,
        paths: list[Path | tuple[str, str]] | None = None,
        loaders: dict | None = None,
    ): ...
    def load(self, default: dict | None = None) -> dict | None: ...
```

### load_config(paths, env_var=None, default=None)

便捷函数。
