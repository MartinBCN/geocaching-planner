from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_database_volume_warning_is_documented() -> None:
    """AC7: the README explains the local volume, the data-loss command, and normal stop/start."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Local services and data", 1)[1].split("\n## ", 1)[0]

    assert "named Docker volume" in section
    assert "docker compose down -v" in section
    assert "deletes" in section
    assert "Stopping the stack normally preserves" in section
