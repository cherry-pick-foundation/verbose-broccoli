"""Public contract checks for the settled discovery and attribution rules."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_discovery_managed_link_contract():
    for relative in (
        "specs/053-jev-mcp-privacy/contracts/registration.md",
        "specs/053-jev-mcp-privacy/spec.md",
    ):
        text = (ROOT / relative).read_text().lower()
        assert "discovery-managed" in text
        assert "pending journal" in text
        assert "foreign targets" in text
        assert "whose bytes differ" in text
        assert "user's own link elsewhere is never touched" in text


def test_notices_exclude_installed_phonenumbers_dependency():
    text = (ROOT / "licenses/third-party-notices.md").read_text()
    assert "## daviddrysdale/python-phonenumbers" not in text
