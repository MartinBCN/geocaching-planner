from pathlib import Path

import httpx
import pytest
import respx

from scripts import brouter_segments as bs

BASE = bs.BASE_URL


@pytest.fixture
def dest(tmp_path: Path) -> Path:
    return tmp_path / "segments"


def test_default_tiles_when_unset() -> None:
    assert bs.parse_tiles(None) == ("E0_N50", "E5_N50")
    assert bs.parse_tiles("   ") == ("E0_N50", "E5_N50")


def test_override_tiles_are_parsed() -> None:
    assert bs.parse_tiles("E5_N50, W10_S3") == ("E5_N50", "W10_S3")


@pytest.mark.parametrize("bad", ["../etc", "E5", "E5_N50/../x", "e5_n50"])
def test_invalid_tile_names_are_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="invalid BROUTER_SEGMENTS"):
        bs.parse_tiles(bad)


@respx.mock
def test_successful_download_is_renamed_and_leaves_no_part_file(dest: Path) -> None:
    respx.get(f"{BASE}E5_N50.rd5").mock(return_value=httpx.Response(200, content=b"x" * 10))

    with httpx.Client() as client:
        results = bs.run(["E5_N50"], dest, client)

    assert [r.status for r in results] == ["downloaded"]
    assert (dest / "E5_N50.rd5").read_bytes() == b"x" * 10
    assert not (dest / "E5_N50.rd5.part").exists()


@respx.mock
def test_failed_download_leaves_no_partial_file_and_is_reported(dest: Path) -> None:
    respx.get(f"{BASE}E5_N50.rd5").mock(return_value=httpx.Response(404))

    with httpx.Client() as client:
        results = bs.run(["E5_N50"], dest, client)

    assert results[0].status == "failed"
    assert not (dest / "E5_N50.rd5").exists()
    assert not (dest / "E5_N50.rd5.part").exists()


@respx.mock
def test_network_error_is_a_failure_not_a_crash(dest: Path) -> None:
    dest.mkdir(parents=True)
    respx.get(f"{BASE}E0_N50.rd5").mock(side_effect=httpx.ConnectError("boom"))

    with httpx.Client() as client:
        result = bs.download_tile(client, "E0_N50", dest)

    assert result.status == "failed"
    assert not (dest / "E0_N50.rd5.part").exists()


@respx.mock
def test_existing_complete_tile_is_skipped_without_request(dest: Path) -> None:
    dest.mkdir(parents=True)
    (dest / "E5_N50.rd5").write_bytes(b"done")
    route = respx.get(f"{BASE}E5_N50.rd5").mock(return_value=httpx.Response(200, content=b"new"))

    with httpx.Client() as client:
        results = bs.run(["E5_N50"], dest, client)

    assert results[0].status == "skipped"
    assert not route.called
    assert (dest / "E5_N50.rd5").read_bytes() == b"done"


@respx.mock
def test_only_configured_tiles_are_requested(dest: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BROUTER_SEGMENTS", "W10_S3")
    monkeypatch.setenv("BROUTER_SEGMENTS_DIR", str(dest))
    wanted = respx.get(f"{BASE}W10_S3.rd5").mock(return_value=httpx.Response(200, content=b"ok"))
    default = respx.get(f"{BASE}E0_N50.rd5").mock(return_value=httpx.Response(200, content=b"no"))

    assert bs.main() == 0

    assert wanted.called
    assert not default.called


@respx.mock
def test_main_exits_nonzero_when_any_tile_fails(
    dest: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("BROUTER_SEGMENTS", "E0_N50,E5_N50")
    monkeypatch.setenv("BROUTER_SEGMENTS_DIR", str(dest))
    respx.get(f"{BASE}E0_N50.rd5").mock(return_value=httpx.Response(200, content=b"ok"))
    respx.get(f"{BASE}E5_N50.rd5").mock(return_value=httpx.Response(500))

    assert bs.main() == 1

    out = capsys.readouterr()
    assert "[1/2] E0_N50.rd5" in out.out
    assert "[2/2] E5_N50.rd5" in out.out
    assert "Summary: 1 downloaded, 0 skipped, 1 failed" in out.out
    assert "FAILED E5_N50.rd5" in out.err


def test_main_rejects_invalid_tile_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("BROUTER_SEGMENTS", "../bad")
    assert bs.main() == 2
    assert "invalid BROUTER_SEGMENTS" in capsys.readouterr().err
