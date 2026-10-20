import pytest


@pytest.fixture
def make_files(tmp_path):
    """Create empty files (and parent dirs) under tmp_path; return tmp_path."""

    def _make(*names, content="x"):
        for name in names:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return tmp_path

    return _make


def snapshot(root):
    """Map every path under root to its content (None for directories)."""
    return {
        str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None)
        for p in sorted(root.rglob("*"))
    }
