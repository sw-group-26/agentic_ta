"""Unit tests for LocalStorageAdapter."""

import json
from pathlib import Path

import pytest

from app.storage import LocalStorageAdapter


@pytest.fixture
def adapter(tmp_path: Path) -> LocalStorageAdapter:
    """Return a LocalStorageAdapter backed by a temporary directory."""
    return LocalStorageAdapter(tmp_path)


class TestSaveFile:
    def test_copies_file_to_object_key_path(
        self, adapter: LocalStorageAdapter, tmp_path: Path
    ):
        # Arrange: create a source file
        src = tmp_path / "source.py"
        src.write_text("print('hello')")
        key = "offering/o1/assignment/hw1/student/S001/attempt/1/hw1.py"

        # Act
        stored = adapter.save_file(src, key)

        # Assert: file physically exists at the returned path
        assert Path(stored).exists()
        assert Path(stored).read_text() == "print('hello')"

    def test_creates_intermediate_directories(
        self, adapter: LocalStorageAdapter, tmp_path: Path
    ):
        src = tmp_path / "a.py"
        src.write_text("x = 1")
        key = "deep/nested/dir/file.py"

        stored = adapter.save_file(src, key)

        assert Path(stored).exists()

    def test_raises_if_source_missing(self, adapter: LocalStorageAdapter):
        with pytest.raises(FileNotFoundError):
            adapter.save_file("/nonexistent/path/file.py", "some/key/file.py")

    def test_returned_path_is_absolute(
        self, adapter: LocalStorageAdapter, tmp_path: Path
    ):
        src = tmp_path / "f.py"
        src.write_text("")
        stored = adapter.save_file(src, "a/b.py")
        assert Path(stored).is_absolute()


class TestSaveJson:
    def test_writes_valid_json(self, adapter: LocalStorageAdapter):
        data = {"submission_id": "abc-123", "score": 95}
        key = "offering/o1/assignment/hw1/student/S001/attempt/1/manifest.json"

        stored = adapter.save_json(data, key)

        loaded = json.loads(Path(stored).read_text(encoding="utf-8"))
        assert loaded == data

    def test_creates_intermediate_directories(self, adapter: LocalStorageAdapter):
        stored = adapter.save_json({"k": "v"}, "a/b/c/data.json")
        assert Path(stored).exists()

    def test_non_ascii_preserved(self, adapter: LocalStorageAdapter):
        data = {"name": "김철수"}
        stored = adapter.save_json(data, "meta.json")
        raw = Path(stored).read_text(encoding="utf-8")
        # ensure_ascii=False — Korean characters should not be escaped
        assert "김철수" in raw


class TestLoadText:
    def test_returns_file_content(self, adapter: LocalStorageAdapter, tmp_path: Path):
        src = tmp_path / "code.py"
        src.write_text("def foo(): pass")
        key = "offering/o1/code.py"
        adapter.save_file(src, key)

        content = adapter.load_text(key)

        assert content == "def foo(): pass"

    def test_raises_if_key_missing(self, adapter: LocalStorageAdapter):
        with pytest.raises(FileNotFoundError):
            adapter.load_text("nonexistent/key.txt")


class TestExists:
    def test_returns_true_for_existing_key(
        self, adapter: LocalStorageAdapter, tmp_path: Path
    ):
        src = tmp_path / "f.txt"
        src.write_text("data")
        key = "dir/f.txt"
        adapter.save_file(src, key)

        assert adapter.exists(key) is True

    def test_returns_false_for_missing_key(self, adapter: LocalStorageAdapter):
        assert adapter.exists("no/such/file.txt") is False

    def test_leading_slash_in_key_handled(
        self, adapter: LocalStorageAdapter, tmp_path: Path
    ):
        src = tmp_path / "x.py"
        src.write_text("")
        # save without slash, check with leading slash
        adapter.save_file(src, "dir/x.py")
        assert adapter.exists("/dir/x.py") is True
