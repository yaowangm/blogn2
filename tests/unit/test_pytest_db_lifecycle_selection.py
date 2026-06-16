"""Tests for pytest database lifecycle selection rules."""

from tests import conftest


class DummyItem:
    def __init__(self, fspath, fixturenames=(), markers=()):
        self.fspath = fspath
        self.fixturenames = list(fixturenames)
        self._markers = set(markers)

    def get_closest_marker(self, name):
        return object() if name in self._markers else None


def test_pure_unit_item_does_not_require_test_database():
    item = DummyItem("tests/unit/test_markdown_utils_js.py")

    assert conftest._item_requires_test_database(item) is False
    assert conftest._selected_items_need_test_database([item]) is False


def test_integration_path_requires_test_database():
    item = DummyItem("tests/integration/test_basic_endpoints.py")

    assert conftest._item_requires_test_database(item) is True


def test_integration_marker_requires_test_database():
    item = DummyItem("tests/unit/test_scripts_password_tools.py", markers=("integration",))

    assert conftest._item_requires_test_database(item) is True


def test_real_database_fixture_requires_test_database():
    item = DummyItem("tests/performance/test_bert_vectorization_performance.py", fixturenames=("real_async_session",))

    assert conftest._item_requires_test_database(item) is True


def test_force_env_requires_test_database(monkeypatch):
    item = DummyItem("tests/unit/test_markdown_utils_js.py")
    monkeypatch.setenv("BLOGN_FORCE_TEST_DB_LIFECYCLE", "true")

    assert conftest._selected_items_need_test_database([item]) is True
