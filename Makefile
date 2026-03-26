# =============================================================================
# 使用说明：
#   - 开发环境：make dev（安装 + pre-commit）
#   - 代码检查：make check（lint + format + typecheck + test）
#   - 发布版本：make release version=X.X.X（自动创建 git tag 和 GitHub Release）
#
# 依赖工具：pip, ruff, mypy, pytest, build, gh
# =============================================================================

PACKAGE := mrconfig

.PHONY: help install install-dev dev test lint format typecheck check build clean bump release

# 显示所有命令及其说明
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | grep -v '.PHONY' | awk -F: '{printf "\033[36m  %-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# 安装命令
# ---------------------------------------------------------------------------

# 安装项目（仅运行时依赖）
install:
	pip install -e .

# 安装项目（包含开发依赖）
install-dev: install
	pip install -e ".[dev]"

# 安装开发环境（依赖 + pre-commit hooks）
dev: install-dev
	pre-commit install
	@echo "开发环境就绪"

# ---------------------------------------------------------------------------
# 测试与检查命令
# ---------------------------------------------------------------------------

# 运行单元测试（带覆盖率报告）
test:
	pytest --cov=$(PACKAGE) --cov-report=term-missing -v

# 代码风格检查（ruff）
lint:
	ruff check $(PACKAGE)/ tests/

# 代码格式化（ruff）
format:
	ruff format $(PACKAGE)/ tests/

# 类型检查（mypy）
typecheck:
	mypy $(PACKAGE)/

# 完整检查（lint + format + typecheck + test）
check: lint format typecheck test

# ---------------------------------------------------------------------------
# 构建与发布命令
# ---------------------------------------------------------------------------

# 构建发布包（sdist + wheel）并安装到本地
build:
	python -m build
	pip install dist/$(PACKAGE)-*.whl --force-reinstall

VERSION_FILE := $(PACKAGE)/__version__.py

# 更新版本号（修改 $(PACKAGE)/__version__.py）
# 用法：make bump version=X.X.X
bump:
	@if [ -z "$(version)" ]; then \
		echo "Usage: make bump version=X.X.X"; \
		exit 1; \
	fi && \
	sed -i 's/^__version__ = ".*"/__version__ = "$(version)"/' $(VERSION_FILE) && \
	echo "Version bumped to $(version) (reads from $(VERSION_FILE))"

# 发布版本（更新版本号 → git commit → git tag → GitHub Release）
# 用法：make release version=X.X.X
# 注意：需要先安装 gh CLI 并登录（gh auth login）
release:
	@if [ -z "$(version)" ]; then \
		echo "Usage: make release version=X.X.X"; \
		exit 1; \
	fi && \
	current=$$(sed -n 's/__version__\s*=\s*"\([^"]*\)"/\1/p' $(VERSION_FILE)) && \
	if [ "$$current" = "$(version)" ]; then \
		echo "当前版本已是 v$(version)，无需更新"; \
	else \
		echo "当前版本: v$$current -> v$(version)"; \
		make bump version=$(version); \
		git add -A && \
		git commit -m "chore: release v$(version)"; \
	fi && \
	git tag -a "v$(version)" -m "Release v$(version)" 2>/dev/null || true && \
	git push && \
	git push origin "v$(version)" && \
	gh release create "v$(version)" --title "v$(version)" --generate-notes 2>/dev/null || echo "Release v$(version) already exists" && \
	echo "Release v$(version) completed"

# ---------------------------------------------------------------------------
# 清理命令
# ---------------------------------------------------------------------------

# 清理构建产物和缓存文件
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .coverage htmlcov/
