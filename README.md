# mrconfig

多路径配置文件加载器，支持 JSON、YAML、TOML 格式

## 安装

```bash
pip install mrconfig
```

## 支持格式

| 格式   | 扩展名             | 说明                    |
|------|-----------------|-----------------------|
| JSON | `.json`         | 标准 JSON 格式            |
| YAML | `.yaml`, `.yml` | YAML 格式               |
| TOML | `.toml`         | TOML 格式（Python 3.11+） |

## 快速开始

### 方式一：应用模式（推荐）

```python
from mrconfig import load_config

# 一步到位，自动搜索配置
config = load_config("my_app")

# 等价于搜索以下路径：
# 1. 环境变量 MY_APP_CONFIG 指定的路径
# 2. 当前目录 .my_app.yaml
# 3. XDG 配置目录下 my-app/config.yaml
```

### 方式二：传统模式

```python
from mrconfig import ConfigLoader

loader = ConfigLoader(name=".myapp.yaml", xdg="app/config.yaml")
config = loader.load(default={"debug": False})
```

## 功能特性

### 路径搜索优先级

1. **环境变量**（最高优先级）- 通过 `{APP}_CONFIG` 环境变量指定
2. **当前目录** - `name` 参数指定的文件
3. **XDG 配置目录** - 平台特定的标准配置路径

### 路径安全

- `~` 自动展开为用户目录
- 路径解析为绝对路径，防止路径遍历攻击
- 符号链接自动解析

### XDG 配置路径

| 平台      | 路径                     |
|---------|------------------------|
| Linux   | `~/.config/{filename}` |
| macOS   | `~/.config/{filename}` |
| Windows | `%APPDATA%\{filename}` |

可通过环境变量覆盖：
- Linux/macOS: `XDG_CONFIG_HOME`
- Windows: `APPDATA`

## API 参考

### ConfigLoader

```python
from mrconfig import ConfigLoader

# 传统初始化
loader = ConfigLoader(
    name=".myapp.yaml",      # 当前目录配置文件
    xdg="app/config.yaml",  # XDG 目录下配置
    env="MYAPP_CONFIG",      # 环境变量（最高优先级）
)

# 应用模式快速创建
loader = ConfigLoader.from_app("my_app")

config = loader.load()
```

#### 核心方法

| 方法                                         | 说明               |
|--------------------------------------------|------------------|
| `load(default=None)`                       | 加载配置，返回字典或默认值    |
| `get_paths()`                              | 获取所有可能的配置路径（已去重） |
| `get_active_path()`                        | 获取实际生效的配置文件路径    |
| `from_app(app, use_env=True, ext=".yaml")` | 从应用名称快速创建加载器     |

### 工具函数

```python
from mrconfig import load_config, load_file, get_active_config_path

# 加载配置（支持应用模式）
config = load_config("my_app")
config = load_config(name=".myapp.yaml")

# 加载指定文件
config = load_file("/path/to/config.yaml")

# 获取生效的配置文件路径
path = get_active_config_path("my_app")
```
