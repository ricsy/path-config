"""测试配置加载"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from mrconfig import (
    ConfigLoader,
    JsonLoader,
    YamlLoader,
    get_active_config_path,
    load_config,
    load_file,
    xdg_config_path,
)


class TestLoaders:
    """各类型加载器测试"""

    def test_json_loader(self) -> None:
        """测试 JSON 加载器"""
        data = {"key": "value", "num": 42}
        loader = JsonLoader()
        result = loader.load(json.dumps(data))
        assert result == data

    def test_yaml_loader(self) -> None:
        """测试 YAML 加载器"""
        data = {"key": "value", "list": [1, 2, 3]}
        loader = YamlLoader()
        result = loader.load(yaml.dump(data))
        assert result == data

    def test_yaml_loader_empty(self) -> None:
        """测试 YAML 加载器处理空文件"""
        loader = YamlLoader()
        result = loader.load("")
        assert result == {}


class TestConfigLoader:
    """ConfigLoader 类测试"""

    def test_load_json_file(self) -> None:
        """测试加载 JSON 文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"format": "json"}, f)
            path = Path(f.name)

        try:
            loader = ConfigLoader(name=path.name)
            loader.paths.insert(0, path)  # 插入到首位优先
            result = loader.load()
            assert result == {"format": "json"}
        finally:
            path.unlink()

    def test_load_name_path(self) -> None:
        """测试 name 参数作为 cwd 路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".test.yaml")
                config_file.write_text("key: value", encoding="utf-8")

                loader = ConfigLoader(name=".test.yaml")
                result = loader.load()
                assert result == {"key": "value"}
            finally:
                os.chdir(old_cwd)

    def test_load_xdg_path(self) -> None:
        """测试 XDG 路径"""
        loader = ConfigLoader(name=".test.yaml", xdg="app/config.yaml")
        assert len(loader.paths) == 2
        assert loader.paths[0].name == ".test.yaml"
        assert "app" in str(loader.paths[1])

    def test_load_env_var_priority(self, monkeypatch) -> None:
        """测试环境变量优先级最高"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("source: env", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            loader = ConfigLoader(env="TEST_CONFIG", name=".test.yaml")
            result = loader.load()
            assert result == {"source": "env"}

    def test_load_default(self, monkeypatch) -> None:
        """测试返回默认值"""
        monkeypatch.delenv("TEST_CONFIG", raising=False)
        loader = ConfigLoader(env="TEST_CONFIG")
        result = loader.load(default={"default": True})
        assert result == {"default": True}

    def test_unsupported_format(self) -> None:
        """测试不支持的文件格式"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write("<config/>")
            path = Path(f.name)

        try:
            loader = ConfigLoader(name=".test.xml")
            loader.paths.insert(0, path)
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load()
        finally:
            path.unlink()


class TestLoadConfig:
    """便捷函数测试"""

    def test_load_from_name(self) -> None:
        """测试从 name 加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".config.yaml")
                config_file.write_text("key: value", encoding="utf-8")

                result = load_config(name=".config.yaml")
                assert result == {"key": "value"}
            finally:
                os.chdir(old_cwd)

    def test_load_env_var(self, monkeypatch) -> None:
        """测试环境变量优先级最高"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("source: env", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            result = load_config(env="TEST_CONFIG", name=".config.yaml")
            assert result == {"source": "env"}

    def test_load_default_when_not_found(self, monkeypatch) -> None:
        """测试未找到时返回默认值"""
        monkeypatch.delenv("TEST_CONFIG", raising=False)
        result = load_config(env="TEST_CONFIG", default={"default": True})
        assert result == {"default": True}


class TestXdgConfigPath:
    """xdg_config_path 测试"""

    def test_xdg_path_fallback(self) -> None:
        """测试 XDG 路径回退到用户目录"""
        result = xdg_config_path("app.yaml")
        assert result.name == "app.yaml"


class TestGetPaths:
    """get_paths 方法测试"""

    def test_get_paths_returns_all_paths(self) -> None:
        """测试返回所有配置的路径"""
        loader = ConfigLoader(name=".test.yaml", xdg="app/config.yaml")
        paths = loader.get_paths()
        assert len(paths) == 2

    def test_get_paths_deduplication(self) -> None:
        """测试路径去重"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "same.yaml"
            config_file.write_text("key: value", encoding="utf-8")

            loader = ConfigLoader(name=config_file.name, xdg=config_file.name)
            loader.paths[0] = config_file  # 替换为同一文件
            loader.paths[1] = config_file

            paths = loader.get_paths()
            # 去重后应该只剩一个
            assert len(paths) == 1

    def test_get_paths_env_first(self, monkeypatch) -> None:
        """测试环境变量路径在最前"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("key: env", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            loader = ConfigLoader(env="TEST_CONFIG", name=".test.yaml")

            paths = loader.get_paths()
            assert str(env_file.resolve()) in str(paths[0])

    def test_get_paths_empty_for_no_config(self) -> None:
        """测试无配置时返回空列表"""
        loader = ConfigLoader()
        assert not loader.get_paths()


class TestGetActivePath:
    """get_active_path 方法测试"""

    def test_get_active_path_env(self, monkeypatch) -> None:
        """测试环境变量指定的路径优先"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("key: env", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            loader = ConfigLoader(env="TEST_CONFIG", name=".other.yaml")

            active = loader.get_active_path()
            assert active is not None
            assert active.resolve() == env_file.resolve()

    def test_get_active_path_name(self, monkeypatch) -> None:
        """测试 name 路径存在时返回"""
        monkeypatch.delenv("TEST_CONFIG", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".test.yaml")
                config_file.write_text("key: name", encoding="utf-8")

                loader = ConfigLoader(name=".test.yaml")
                active = loader.get_active_path()
                assert active is not None
                assert active.name == ".test.yaml"
            finally:
                os.chdir(old_cwd)

    def test_get_active_path_none_when_not_exists(self) -> None:
        """测试路径都不存在时返回 None"""
        loader = ConfigLoader(name=".nonexistent.yaml")
        assert loader.get_active_path() is None


class TestLoadFile:
    """load_file 工具函数测试"""

    def test_load_file_json(self) -> None:
        """测试加载 JSON 文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"key": "json"}, f)
            path = Path(f.name)

        try:
            result = load_file(path)
            assert result == {"key": "json"}
        finally:
            path.unlink()

    def test_load_file_yaml(self) -> None:
        """测试加载 YAML 文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"key": "yaml"}, f)
            path = Path(f.name)

        try:
            result = load_file(path)
            assert result == {"key": "yaml"}
        finally:
            path.unlink()

    def test_load_file_expanduser(self) -> None:
        """测试 ~ 展开"""
        home = Path.home()
        test_file = home / ".test_mrconfig_expand.json"
        test_file.write_text('{"key": "expanded"}', encoding="utf-8")

        try:
            result = load_file("~/.test_mrconfig_expand.json")
            assert result == {"key": "expanded"}
        finally:
            test_file.unlink(missing_ok=True)

    def test_load_file_not_found(self) -> None:
        """测试文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            load_file("/nonexistent/path/config.json")

    def test_load_file_unsupported_format(self) -> None:
        """测试不支持的文件格式"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as f:
            f.write("<config/>")
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="不支持的文件格式"):
                load_file(path)
        finally:
            path.unlink()

    def test_load_file_resolve_symlink(self) -> None:
        """测试解析符号链接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_file = Path(tmpdir) / "real.json"
            real_file.write_text('{"key": "real"}', encoding="utf-8")

            link_file = Path(tmpdir) / "link.json"
            link_file.symlink_to(real_file)

            result = load_file(link_file)
            assert result == {"key": "real"}

    def test_load_file_path_traversal_attack(self) -> None:
        """测试路径遍历攻击被阻止"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置文件
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text('{"key": "config"}', encoding="utf-8")

            # 尝试路径遍历攻击
            attack_path = Path(tmpdir) / ".." / ".." / ".." / ".." / "etc" / "passwd"
            # 即使文件不存在，也不应该抛出异常，而应该返回 FileNotFoundError
            with pytest.raises(FileNotFoundError):
                load_file(attack_path)

    def test_load_file_absolute_path(self) -> None:
        """测试绝对路径"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"key": "absolute"}, f)
            path = Path(f.name).resolve()

        try:
            result = load_file(str(path))
            assert result == {"key": "absolute"}
        finally:
            path.unlink()


class TestGetActiveConfigPath:
    """get_active_config_path 工具函数测试"""

    def test_get_active_config_path_env(self, monkeypatch) -> None:
        """测试环境变量优先级"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("key: env", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            result = get_active_config_path(env="TEST_CONFIG", name=".other.yaml")
            assert result is not None
            assert result.resolve() == env_file.resolve()

    def test_get_active_config_path_name(self, monkeypatch) -> None:
        """测试 name 路径"""
        monkeypatch.delenv("TEST_CONFIG", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".test.yaml")
                config_file.write_text("key: value", encoding="utf-8")

                result = get_active_config_path(name=".test.yaml")
                assert result is not None
                assert result.name == ".test.yaml"
            finally:
                os.chdir(old_cwd)

    def test_get_active_config_path_none(self) -> None:
        """测试路径都不存在时返回 None"""
        result = get_active_config_path(name=".nonexistent.yaml")
        assert result is None

    def test_get_active_config_path_app(self, monkeypatch) -> None:
        """测试 app 参数"""
        monkeypatch.delenv("TEST_APP_CONFIG", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".test_app.yaml")
                config_file.write_text("key: value", encoding="utf-8")

                result = get_active_config_path(app="test_app")
                assert result is not None
                assert result.name == ".test_app.yaml"
            finally:
                os.chdir(old_cwd)

    def test_get_active_config_path_app_env_priority(self, monkeypatch) -> None:
        """测试 app 模式下环境变量优先级"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("key: env", encoding="utf-8")

            monkeypatch.setenv("MYAPP_CONFIG", str(env_file))
            result = get_active_config_path(app="myapp", use_env=True)
            assert result is not None
            assert result.resolve() == env_file.resolve()


class TestPathSecurity:
    """路径安全测试"""

    def test_resolve_prevents_traversal(self) -> None:
        """测试 resolve() 防止路径遍历并正确解析路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text('{"key": "safe"}', encoding="utf-8")

            # 使用 .. 构造路径，但最终仍指向同一文件
            attack_path = Path(tmpdir) / "subdir" / ".." / "config.json"
            assert attack_path.resolve() == config_file.resolve()

            result = load_file(attack_path)
            assert result == {"key": "safe"}

    def test_expanduser_in_config_loader(self) -> None:
        """测试 ConfigLoader 展开用户目录"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"key": "home"}, f)
            path = Path(f.name)

        try:
            loader = ConfigLoader(name=f"~/{path.name}")
            # 验证路径已被展开为绝对路径
            assert loader.paths[0].is_absolute()
            assert loader.paths[0].name == path.name
        finally:
            path.unlink()


class TestFromApp:
    """from_app 类方法测试"""

    def test_from_app_basic(self) -> None:
        """测试基本用法（use_env=False）"""
        loader = ConfigLoader.from_app("test_backup", use_env=False)

        assert loader.env is None
        assert len(loader.paths) == 2
        assert loader.paths[0].name == ".test_backup.yaml"
        assert loader.paths[1].name == "config.yaml"

    def test_from_app_with_env(self) -> None:
        """测试启用环境变量"""
        loader = ConfigLoader.from_app("test_backup", use_env=True)

        assert loader.env == "TEST_BACKUP_CONFIG"

    def test_from_app_kebab_case(self) -> None:
        """测试下划线转短横线"""
        loader = ConfigLoader.from_app("my_app_name")

        assert loader.paths[0].name == ".my_app_name.yaml"
        assert "my-app-name" in str(loader.paths[1])

    def test_from_app_without_env(self) -> None:
        """测试禁用环境变量"""
        loader = ConfigLoader.from_app("my_app", use_env=False)

        assert loader.env is None

    def test_from_app_custom_ext(self) -> None:
        """测试自定义扩展名"""
        loader = ConfigLoader.from_app("my_app", ext=".json")

        assert loader.paths[0].name == ".my_app.json"
        assert loader.paths[1].name == "config.json"


class TestLoadConfigApp:
    """load_config app 模式测试"""

    def test_load_config_app_from_name(self, monkeypatch) -> None:
        """测试从 name 加载"""
        monkeypatch.delenv("MY_APP_CONFIG", raising=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_file = Path(".my_app.yaml")
                config_file.write_text("key: value", encoding="utf-8")

                result = load_config("my_app")
                assert result == {"key": "value"}
            finally:
                os.chdir(old_cwd)

    def test_load_config_app_env_priority(self, monkeypatch) -> None:
        """测试环境变量优先级"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("source: env", encoding="utf-8")

            monkeypatch.setenv("TEST_APP_CONFIG", str(env_file))
            result = load_config("test_app", use_env=True)
            assert result == {"source": "env"}

    def test_load_config_app_default(self) -> None:
        """测试返回默认值"""
        result = load_config("nonexistent_app", default={"default": True})
        assert result == {"default": True}
