import hashlib
import socket
import sys
from contextlib import contextmanager

import pytest


sys.dont_write_bytecode = True


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")


@pytest.fixture
def unchanged():
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
