"""
Docker entrypoint 脚本检查

确保 entrypoint 中 uvicorn 以 gosu appuser 运行，不以 root 运行。
"""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_entrypoint_runs_uvicorn_with_gosu_appuser():
    """entrypoint 中 exec uvicorn 前使用 gosu appuser，避免容器内以 root 运行"""
    root = Path(__file__).resolve().parent.parent.parent
    path = root / "docker" / "docker-entrypoint.sh"
    content = path.read_text(encoding="utf-8")
    assert "gosu appuser" in content, "entrypoint 应包含 gosu appuser 以非 root 运行 uvicorn"
    assert "exec gosu appuser env" in content, "exec uvicorn 应以 gosu appuser 调用"
