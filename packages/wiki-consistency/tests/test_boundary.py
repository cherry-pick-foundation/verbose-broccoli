import json
from pathlib import Path

from test_prepare import _prepare, _ready


def test_prepare_requests_exclude_configuration_state_and_credentials(
    tmp_path, monkeypatch
):
    instance, cache, env = _ready(tmp_path)
    marker = "SYNTHETIC-PRIVATE-MARKER-6f6c"
    roots = {
        "XDG_CONFIG_HOME": tmp_path / "xdg-config",
        "XDG_STATE_HOME": tmp_path / "xdg-state",
        "XDG_DATA_HOME": Path(env["XDG_DATA_HOME"]),
    }
    for key, root in roots.items():
        monkeypatch.setenv(key, str(root))
    files = [
        roots["XDG_CONFIG_HOME"] / "verbose-broccoli" / "config.toml",
        roots["XDG_STATE_HOME"] / "verbose-broccoli" / "state.json",
        roots["XDG_CONFIG_HOME"] / "verbose-broccoli" / "credentials.json",
        roots["XDG_DATA_HOME"] / "verbose-broccoli" / "credentials.json",
    ]
    for path in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(marker, encoding="utf-8")

    result = _prepare(instance, cache, scope="lint")

    assert marker not in json.dumps(result["requests"], ensure_ascii=False)
