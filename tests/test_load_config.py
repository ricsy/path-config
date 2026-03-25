"""测试配置加载"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from path_config import ConfigLoader, JsonLoader, YamlLoader, load_config, xdg_config_path


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
            loader = ConfigLoader(path=path)
            result = loader.load()
            assert result == {"format": "json"}
        finally:
            path.unlink()

    def test_load_yaml_file(self) -> None:
        """测试加载 YAML 文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"format": "yaml"}, f)
            path = Path(f.name)

        try:
            loader = ConfigLoader(path=path)
            result = loader.load()
            assert result == {"format": "yaml"}
        finally:
            path.unlink()

    def test_load_xdg_path(self) -> None:
        """测试 XDG 路径"""
        loader = ConfigLoader(xdg="test.yaml")
        assert len(loader.paths) == 1
        assert "test.yaml" in str(loader.paths[0])

    def test_load_cwd_path(self) -> None:
        """测试当前目录路径"""
        loader = ConfigLoader(cwd=".test.yaml")
        assert len(loader.paths) == 1
        assert loader.paths[0].name == ".test.yaml"

    def test_load_env_var_priority(self, monkeypatch) -> None:
        """测试环境变量优先级最高"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"source": "env"}, f)
            env_path = Path(f.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"source": "local"}, f)
            local_path = Path(f.name)

        try:
            monkeypatch.setenv("TEST_CONFIG_PATH", str(env_path))
            loader = ConfigLoader(env_var="TEST_CONFIG_PATH", path=local_path)
            result = loader.load()
            assert result == {"source": "env"}
        finally:
            env_path.unlink()
            local_path.unlink()

    def test_load_fallback(self, monkeypatch) -> None:
        """测试回退到路径列表"""
        monkeypatch.delenv("TEST_CONFIG_PATH", raising=False)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump({"fallback": True}, f)
            path = Path(f.name)

        try:
            loader = ConfigLoader(env_var="TEST_CONFIG_PATH", path=path)
            result = loader.load()
            assert result == {"fallback": True}
        finally:
            path.unlink()

    def test_load_default(self, monkeypatch) -> None:
        """测试返回默认值"""
        monkeypatch.delenv("TEST_CONFIG_PATH", raising=False)
        loader = ConfigLoader(env_var="TEST_CONFIG_PATH", path=Path("/nonexistent"))
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
            loader = ConfigLoader(path=path)
            with pytest.raises(ValueError, match="Unsupported file format"):
                loader.load()
        finally:
            path.unlink()


class TestLoadConfig:
    """便捷函数测试"""

    def test_load_from_path(self) -> None:
        """测试从路径加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("key: value", encoding="utf-8")

            result = load_config(path=config_file)
            assert result == {"key": "value"}

    def test_load_env_var(self, monkeypatch) -> None:
        """测试环境变量优先级最高"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / "env.yaml"
            env_file.write_text("source: env", encoding="utf-8")

            local_file = Path(tmpdir) / "local.yaml"
            local_file.write_text("source: local", encoding="utf-8")

            monkeypatch.setenv("TEST_CONFIG", str(env_file))
            result = load_config(path=local_file, env_var="TEST_CONFIG")
            assert result == {"source": "env"}

    def test_load_default_when_not_found(self, monkeypatch) -> None:
        """测试未找到时返回默认值"""
        monkeypatch.delenv("TEST_CONFIG", raising=False)
        result = load_config(
            path=Path("/nonexistent"), env_var="TEST_CONFIG", default={"default": True}
        )
        assert result == {"default": True}


class TestXdgConfigPath:
    """xdg_config_path 测试"""

    def test_xdg_path_fallback(self) -> None:
        """测试 XDG 路径回退到用户目录"""
        result = xdg_config_path("app.yaml")
        assert result.name == "app.yaml"
