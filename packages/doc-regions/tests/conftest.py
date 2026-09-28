"""Fixtures shared by the doc-regions tests."""

from contextlib import contextmanager
import hashlib
import socket
import sys

import pytest

sys.dont_write_bytecode = True


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Block network access and bytecode writes during each test."""

    def blocked(*args, **kwargs):
        del args, kwargs  # Unused.
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")


@pytest.fixture
def unchanged():
    """Return a context manager that checks a tree's file hashes."""

    def hashes(root):
        return {
            str(path.relative_to(root)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in root.rglob("*")
            if path.is_file()
        }

    @contextmanager
    def check(root):
        before = hashes(root)
        yield
        assert hashes(root) == before

    return check
