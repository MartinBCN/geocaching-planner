from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_brouter_coverage_is_documented() -> None:
    """AC6: README routing section covers tile naming, coverage, download, disk usage, data loss."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Local services and data", 1)[1].split("\n## ", 1)[0]

    assert "south-west corner" in section
    assert "E0_N50" in section
    assert "E5_N50" in section
    assert "0\u201310\u00b0E, 50\u201355\u00b0N" in section
    assert "BROUTER_SEGMENTS" in section
    assert "mise run brouter:segments" in section
    assert "outside" in section
    assert "MB" in section or "GB" in section or "disk" in section
    assert "docker compose down -v" in section
