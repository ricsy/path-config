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
from path_config import ConfigLoader

# 简单用法：当前目录 + XDG 目录
loader = ConfigLoader(name=".myapp.yaml", xdg="app/config.yaml")
config = loader.load(default={"debug": False})
```

### 参数说明

| 参数     | 说明                      |
|--------|-------------------------|
| `name` | 当前目录下的配置文件名（默认 `.yaml`） |
| `xdg`  | XDG 配置目录下的路径            |
| `env`  | 环境变量名，指向配置文件路径（最高优先级）   |

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
        name: str | None = None,
        xdg: str | None = None,
        env: str | None = None,
        loaders: dict | None = None,
    ): ...
    def load(self, default: dict | None = None) -> dict | None: ...
```

### load_config(name=None, xdg=None, env=None, default=None)

便捷函数。
